def find_number(image):
    from imutils import contours
    import numpy as np
    import imutils
    import cv2
    import matplotlib.pyplot as plt
    import warnings
    warnings.filterwarnings('ignore')
    
    FIRST_NUMBER = {
        "3": "American Express",
        "4": "Visa",
        "5": "MasterCard",
        "6": "Discover Card"
    }

    ref = cv2.imread("images/ocr_a_reference.png")

    ref = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)               
    ref = cv2.threshold(ref, 10, 255, cv2.THRESH_BINARY_INV)[1]

    refCnts = cv2.findContours(ref.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    refCnts = refCnts[1] if imutils.is_cv3() else refCnts[0]
    refCnts = contours.sort_contours(refCnts, method="left-to-right")[0]

    digits = {}


    for (i, c) in enumerate(refCnts):
        (x, y, w, h) = cv2.boundingRect(c)
        roi = ref[y:(y + h), x:(x + w)]
        roi2 = cv2.resize(roi, (57, 88))
        digits[i] = roi
        
    
    rectKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 3))
    sqKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    image = imutils.resize(image, width=300)

    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, rectKernel)
    gradX = cv2.Sobel(tophat, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
    gradX = np.absolute(gradX)
    (minVal, maxVal) = (np.min(gradX), np.max(gradX))
    gradX = (255 * ((gradX - minVal) / (maxVal - minVal)))
    gradX = gradX.astype("uint8")

    gradX = cv2.morphologyEx(gradX, cv2.MORPH_CLOSE, rectKernel)
    thresh = cv2.threshold(gradX, 0, 255,cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, sqKernel)

    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[1] if imutils.is_cv3() else cnts[0]


    locs=[]

    for (i, c) in enumerate(cnts):
        (x, y, w, h) = cv2.boundingRect(c)
        ar = w / float(h)
        if ar > 2.5 and ar < 4.5:
            if (w > 40 and w < 70) and (h > 10 and h < 20):
                locs.append((x, y, w, h))
            
    locs = sorted(locs, key=lambda x:x[0])

    output=[]


    for (i, (gX, gY, gW, gH)) in enumerate(locs):
    
        groupOutput = []
 
        group = gray[gY - 5:gY + gH + 5, gX - 5:gX + gW + 5]
        group = cv2.threshold(group, 0, 255,cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
 
        digitCnts = cv2.findContours(group.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)
    
        digitCnts = digitCnts[1] if imutils.is_cv3() else digitCnts[0]
    
        digitCnts = contours.sort_contours(digitCnts,
        method="left-to-right")[0]

       
        for c in digitCnts:
            (x, y, w, h) = cv2.boundingRect(c)
            roi = group[y:y + h, x:x + w]
            roi = cv2.resize(roi, (57, 88))
            scores = []
 
        
            for (digit, digitROI) in digits.items():
            # apply correlation-based template matching, take the
            # score, and update the scores list
                result = cv2.matchTemplate(roi, digitROI,
                                           cv2.TM_CCOEFF)
                (_, score, _, _) = cv2.minMaxLoc(result)
                scores.append(score)
            groupOutput.append(str(np.argmax(scores)))
        
            cv2.rectangle(image, (gX - 5, gY - 5),
                      (gX + gW + 5, gY + gH + 5), (0, 0, 255), 2)
            cv2.putText(image, "".join(groupOutput), (gX, gY - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)
 
    
        output.extend(groupOutput)
    
    print("Credit Card Type: {}".format(FIRST_NUMBER[output[0]]))
    print("Credit Card #: {}".format("".join(output)))
    