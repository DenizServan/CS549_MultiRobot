# perception/cnn/train.py

Trains the CNN, calibrates its confidence, saves cnn_weights.pt.

## main (command line: --data NAME [NAME ...], --epochs [25])

1. seed numpy and torch with 0 ; sym180 = from loadTemplates ; data files default: train_a train_b (task scenes)
2. Split the data
   1. for each data file: samples = loadSamples(name)   (keeps label >= 0 and not cut)
   2. held = the last 20 % of that file's scene seeds -> validation ; the rest -> training
3. net = Net() ; AdamW (lr 2e-3, weight decay 1e-4) ; one-cycle schedule (peak 3e-3)
4. for each epoch:
   1. shuffle the training samples
   2. for each batch of 64:
      1. images, labels, angle targets = getBatch(batch, sym180, rng)   (augmented)
      2. symbol scores, angle scores = net(images)
      3. loss = cross-entropy(symbol) + cross-entropy(angle, soft target)
      4. backprop, optimizer step, schedule step
   3. acc = share of validation rows that are right (validate)
   4. print loss and acc ; if best acc so far: keep a copy of the weights
5. load the best weights
6. calibration = getCalibration(validate(net, validation set))   (same validation set used to pick the epoch)
7. save {weights, calibration, validation accuracy} to cnn_weights.pt

## augment(sample, rng)
1. th = random angle ; keep = random share in (0.35, 1.0) ; shift = N(0, 8 mm) in x and y
2. with probability 0.4: addFakeCover
   1. pick a random outline point c and radius r in (4, 10 cm)
   2. skip if the disc would hide more than half the outline
   3. remove outline and dot points inside the disc ; add a 5 mm grid of the disc to hidden
3. thin outline and dots to `keep` ; turn all points by th ; jitter 2 mm ; add shift
4. return outline, dots, hidden, yaw + th

## getBatch(samples, sym180, rng)
1. for each sample: augment if rng is given ; image = getInputImage ; label ; angle target = getAngleTarget(yaw, sym180[label])
2. return tensors

## validate(net, samples, sym180)
1. for each sample (no augmentation): probabilities ; k = argmax ; margin, b = getMargins
2. right = (k == label) and bin b's angle within 10 deg of yaw (or 180 deg if sym180)
3. return rows (right, margin, far|close)

## getCalibration(rows)
1. m_accept = getMarginThreshold(close rows, 1 %): walk margins from high to low, keep the lowest where the wrong share <= 1 %
2. m_act = max(getMarginThreshold(far rows, 3 %), m_accept + 0.01)
3. points: 0 -> 0, m_accept / 2 -> CONF_VERIFY, m_accept -> CONF_ACCEPT, m_act -> CONF_ACT, 1 -> 1
4. return {margin, conf}
> The CONF_* values are read from parameters.py at training time; changing them later needs a retrain.
