"""
Runs the whole task (two robots search, re-read, grasp and spell the sentence) with THIS perception package plugged
into the team's motion planning and coordination code (spell_search/ of the team repository).

    python3 perception/robot_run.py --reader cnn --headless                    # CNN reader, no viewer
    python3 perception/robot_run.py --reader template --seed 3 --sentence "AB12 XY9"
    python3 perception/robot_run.py --team /path/to/CS549_MultiRobot/spell_search --reader cnn

Every other option is passed on to the team's run.py unchanged: --seed, --sentence, --headless, --time, --json,
--video, --no-monitor, --no-clear, --no-reread.

How it plugs in: the robots call agents.read(world, tpl, camera, exclude) for every mast scan and wrist re-read.
That one function is replaced by readForRobots below, which runs reader.readPicture and renames the fields to what
the team's shared map expects. Everything else (scene, cameras, planning, coordination, scoring) is the team's code.
Their scene is the same as ours (same place_characters.py, same camera frames), so the camera names match.
Note: the team's code places pieces using the true in-hand pose (red flag in the review); perception errors therefore
show up as wrong pieces, failed grasps and rejected re-reads, not as a wrong final angle.
"""
import os
import sys
import argparse
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)                                    # this package first: parameters, reader, ...
import parameters as prm
from templates import loadTemplates
from reader import readPicture
from classify_template import classifyTemplate
from ground_truth import getTruth, matchRead, isRight


def getClassifier(name):
    """
    Returns the reader's classifier: the template matcher or the CNN.
    """
    if name == "cnn":
        # imported from cnn/ directly: the team's folder has its own cnn.py, which would hide our cnn/ package
        sys.path.insert(0, os.path.join(HERE, "cnn"))
        from classify_cnn import CnnClassifier
        return CnnClassifier()
    return classifyTemplate


def makeRobotReader(templates, classifier, rows):
    """
    Returns a function with the signature the team's robots call, read(world, tpl, camera, exclude) -> list of reads,
    that runs this package's reader. tpl and exclude are the team's and are not needed: this package has its own
    templates and computes the ignore regions from the scene.
    Every read is also checked against the ground truth and appended to rows (camera, conf, right), only for the
    summary at the end: the robots never see it.
    """
    def readForRobots(world, tpl, camera, exclude):
        reads = readPicture(world.view_cam, world.C, camera, templates, world.floor_top, classifier)
        truth = getTruth(world.C, world.pieces)
        for r in reads:
            piece = matchRead(r, truth)
            rows.append({"camera": "wrist" if "wrist" in camera else "mast", "conf": float(r["conf"]),
                         "right": bool(isRight(r, piece, templates)), "symbol": r["symbol"],
                         "true": None if piece is None else piece["symbol"],
                         "yaw_err": None if piece is None else float(np.degrees(abs((r["yaw"] - piece["yaw"] + np.pi) % (2 * np.pi) - np.pi))),
                         "xy": [float(v) for v in r["xy"]], "z_top": float(r["z_top"]), "tilt": float(r["tilt"])})
        return [{"symbol": r["symbol"], "yaw": r["yaw"], "xy": np.asarray(r["xy"], float), "conf": r["conf"],
                 "z_top": r["z_top"], "stacked": r["stacked"], "prec": r["precision"], "alts": r["alts"]}
                for r in reads]
    return readForRobots


def printReadSummary(rows):
    """
    Prints, per camera, how many reads the robots made, how many were above the threshold they act on and how many of
    those were wrong, and the threshold evaluate.getThreshold would measure from these in-task reads.
    """
    from evaluate import getThreshold
    print("\nperception during the task (checked against ground truth):")
    for camera, limit, target in (("mast", prm.ROBOT_THRESHOLDS_USED[0], prm.TARGET_ERROR_FAR),
                                  ("wrist", prm.ROBOT_THRESHOLDS_USED[2], prm.TARGET_ERROR_CLOSE)):
        r = [x for x in rows if x["camera"] == camera]
        if not r:
            continue
        trusted = [x for x in r if x["conf"] >= limit]
        wrong = sum(not x["right"] for x in trusted)
        print(f"  {camera:5s}: {len(r)} reads, {len(trusted)} trusted (conf >= {limit:.3f}), {wrong} of them wrong; "
              f"measured threshold for <= {100 * target:.0f}% wrong: {getThreshold(r, target):.3f}")


def setThresholds(modules, reader_name):
    """
    The team's robots decide with three confidence thresholds (CONF_ACT, CONF_VERIFY, CONF_ACCEPT) that were measured
    for THEIR reader. Each reader has its own confidence scale, so the values measured for ours (evaluate.py on the
    tuning seeds) replace them in every team module that uses them.
    """
    act, verify, accept = prm.READER_THRESHOLDS[reader_name]
    prm.ROBOT_THRESHOLDS_USED = (act, verify, accept)
    for m in modules:
        m.CONF_ACT, m.CONF_VERIFY, m.CONF_ACCEPT = act, verify, accept
    print(f"perception: thresholds CONF_ACT {act:.3f}, CONF_VERIFY {verify:.3f}, CONF_ACCEPT {accept:.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--reader", choices=["template", "cnn"], default="cnn")
    ap.add_argument("--team", default=prm.TEAM_SPELL_SEARCH_PATH)
    args, team_args = ap.parse_known_args()
    if not os.path.isfile(os.path.join(args.team, "agents.py")):
        raise FileNotFoundError(f"team code not found at {args.team} (give --team /path/to/spell_search)")

    sys.path.insert(1, args.team)                           # the team's modules: agents, planning, run, ...
    import agents
    import coordination
    import run as team_run

    rows = []
    agents.read = makeRobotReader(loadTemplates(), getClassifier(args.reader), rows)
    setThresholds([agents, coordination], args.reader)
    print(f"perception: this package's {args.reader} reader plugged into the team's robots")
    sys.argv = [os.path.join(args.team, "run.py")] + [a for a in team_args if a != "--cnn"]
    try:
        team_run.main()
    finally:
        printReadSummary(rows)
        if os.environ.get("ROBOT_RUN_ROWS"):                # debugging: keep every in-task read
            import json
            json.dump(rows, open(os.environ["ROBOT_RUN_ROWS"], "w"))
