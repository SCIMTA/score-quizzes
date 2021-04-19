import os
from time import time

import cv2
import numpy as np
import torch
import torchvision.transforms.functional as TF
from PIL import Image
from torch.autograd import Variable

from u2net_test import net

model_name = 'u2net'


def norm_pred(d):
    ma = torch.max(d)
    mi = torch.min(d)

    dn = (d - mi) / (ma - mi)

    return dn


def get_output(pred, image_ori, image_name="cache.png"):
    predict = pred
    predict = predict.squeeze()
    predict_np = predict.cpu().data.numpy()
    im = Image.fromarray(predict_np * 255).convert('RGB')
    img_name = image_name.split(os.sep)[-1]
    image = image_ori[:, :, ::-1]
    imo = im.resize((image.shape[1], image.shape[0]), resample=Image.BILINEAR)
    aaa = img_name.split(".")
    bbb = aaa[0:-1]
    imidx = bbb[0]
    for i in range(1, len(bbb)):
        imidx = imidx + "." + bbb[i]
    mask = np.array(imo)
    mask = mask[:, :, ::-1].copy()
    contours, _ = cv2.findContours(cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    x, y, w, h = (0, 0, 0, 0)
    if len(contours) > 0:
        con = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(con)

    mask_out = cv2.subtract(mask, image_ori)

    mask_out = cv2.subtract(mask, mask_out)

    ret, thresh = cv2.threshold(mask, 100, 255, cv2.THRESH_BINARY)
    mask_out[(thresh == 0).all(-1)] = [255, 255, 255]
    # cv2.imshow('mask_out', cv2.resize(mask_out, (500, 666)))
    # cv2.imshow('mask', cv2.resize(mask, (500, 666)))
    # cv2.waitKey()
    img_file_out_name = str(int(time())) + ".jpg"
    return mask_out[y:y + h, x:x + w], img_file_out_name


def using_u2net(img):
    inputs_test = Image.fromarray(img)
    inputs_test = TF.to_tensor(inputs_test)
    inputs_test = TF.resize(inputs_test, [320, 320])
    inputs_test.unsqueeze_(0)
    inputs_test = inputs_test.type(torch.FloatTensor)
    if torch.cuda.is_available():
        inputs_test = Variable(inputs_test.cuda())
    else:
        inputs_test = Variable(inputs_test)
    d1, d2, d3, d4, d5, d6, d7 = net(inputs_test)
    # normalization
    pred = d1[:, 0, :, :]
    pred = norm_pred(pred)
    # save results to test_results folder
    del d1, d2, d3, d4, d5, d6, d7
    return get_output(pred, img)
