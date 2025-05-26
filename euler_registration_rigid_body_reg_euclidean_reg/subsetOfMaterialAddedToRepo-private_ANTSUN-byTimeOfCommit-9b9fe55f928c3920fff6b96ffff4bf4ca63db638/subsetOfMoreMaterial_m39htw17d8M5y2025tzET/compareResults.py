


functToGetName=(lambda y: f"/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t{int(y):04d}_ch2.nrrd");
import numpy as np;    

import nrrd;

import euler_gpu;


#V~V~V~V~V~V~V~V~V~V~V~V~V~V~V~V~V~V~V~V~V~V~V~V~V
# From Euler GPU:
# git@github.com:flavell-lab/euler_gpu.git
# commit b7ada1272017d52e68e69e25cf5fd5c891b06298
# file: gncc.py
# lines 43 to 50, inclusive of both  
#=================================================


def calculate_gncc(fixed, moving, epsForStability=0): # 1e-8):

    mu_f = np.mean(fixed)
    mu_m = np.mean(moving)
    a = np.sum((fixed - mu_f) * (moving - mu_m))
    b = np.sqrt(np.sum((fixed - mu_f) ** 2) * np.sum((moving - mu_m) ** 2)+epsForStability)

    return a / b

#^_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^^_^_^





def readPath(path):
    return nrrd.read(path)[0];


def readForANTSUNCurrent(path):
    moving, fixed= [int(x) for x in path.split("/")[-2].split("to")];

    fixedImg=readPath(functToGetName(fixed));
    movingImg=readPath(path);


    fixedImg_downSampled_xy= euler_gpu.max_intensity_projection_and_downsample(fixedImg, 4, projection_axis=2)
    movingImg_downSampled_xy= euler_gpu.max_intensity_projection_and_downsample(movingImg, 4, projection_axis=2)
    fixedImg_downSampled_xz= euler_gpu.max_intensity_projection_and_downsample(fixedImg, 4, projection_axis=1)
    movingImg_downSampled_xz= euler_gpu.max_intensity_projection_and_downsample(movingImg, 4, projection_axis=1)
    print("current:"+str((moving, fixed)) + ":" +  str((movingImg.shape,fixedImg.shape))   +","+\
        str(calculate_gncc(fixedImg,movingImg)) + "," + \
        str(calculate_gncc(fixedImg_downSampled_xy,movingImg_downSampled_xy)) + "," + \
        str(calculate_gncc(fixedImg_downSampled_xz,movingImg_downSampled_xz)) ,flush=True);

    return;


listFile="/store1/david/euler_reg_d22M2y2025tzET/data/logsFromExperimentingAndDevelopingEulerRegistrationStillSittingAround_s30m09htw19d17M03y2025tzUTC/eulerResultsFromCurrentApproach_s32m09htw18d11M03y2025tzUTC.txt";
fh=open(listFile, "r");
thingsToRun=[]
while(True): 
    thisLine= fh.readline().replace("\n","");
    if(len(thisLine) == 0 ):
        break;
    thingsToRun.append(thisLine);

from multiprocessing import Pool

with Pool(128) as p:
    p.map(readForANTSUNCurrent, thingsToRun);

fh.close();


