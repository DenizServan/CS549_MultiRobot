# perception/cnn/classify_cnn.py

CNN reader with the same inputs and outputs as classifyTemplate.

## CnnClassifier.__init__(path = cnn_weights.pt)

1. saved = torch.load(path)
2. n_layers = input channels of the first conv in the saved weights (2 for old weights, 3 with the hidden layer)
3. net = Net(n_layers) ; load the weights ; eval mode
4. calibration = saved["calibration"]

## CnnClassifier.__call__(desc, templates)

1. image = getInputImage(top - centre, dark - centre, hidden - centre)
2. symbol scores, angle scores = net(image[:n_layers]) ; p_symbol, p_angle = softmax of each
3. k = argmax p_symbol
4. margin, b = getMargins(p_symbol, p_angle, sym180[k])
   1. b = argmax p_angle
   2. around(c) = sum of p_angle over bins c-2 .. c+2
   3. flipped = 0 if sym180 else around(b + 36)        (mass at the half-turned angle)
   4. symbol_margin = best - second symbol probability
   5. margin = min(symbol_margin, around(b) - flipped)
5. yaw = circular mean of the bin angles b-2 .. b+2 weighted by p_angle
6. alts = up to 3 other symbols with probability > CNN_MIN_RUNNER_UP_PROB [0.1]
7. return {k, yaw, margin = calibrate(margin, calibration), alts, fit_check = True}
> fit_check = True makes reader.py multiply by fitPenalty (template fit of the CNN's answer).
