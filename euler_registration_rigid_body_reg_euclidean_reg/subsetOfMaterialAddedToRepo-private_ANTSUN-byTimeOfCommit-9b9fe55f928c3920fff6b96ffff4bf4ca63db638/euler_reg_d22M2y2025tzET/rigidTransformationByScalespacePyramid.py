

from PIL import Image
from multiprocessing import Pool
from skimage.transform import pyramid_gaussian
from typing import List, Tuple, Any, NamedTuple, Dict;
import euler_gpu; 
import itertools;
import nrrd;
import numpy as np;
import os;
import sys;
import time;
import torch; 

# Note that the values in the block below appear to be 
# required to be strings, even if they convey integers.
for (k,v) in [ ("MKL_NUM_THREADS", "2"), 
               ("NUMEXPR_NUM_THREADS", "2"),
               ("OMP_NUM_THREADS", "2")]:
    os.environ[k] = v;




def requires(boolStatement):
    assert(boolStatement);

def ensures(boolStatement):
    assert(boolStatement);



class PreprocessedImgStruct(): #NamedTuple):
    def __init__(self, filePath, frameNumber):
        requires(isinstance(frameNumber, int));
        requires(frameNumber >= 0);
        requires(isinstance(filePath,str));
        requires(len(filePath) > 0);
        self.no_z : List[np.ndarray] =generateFeaturePyramid(filePath, axes="projectedOut_z");
        self.no_y : List[np.ndarray] =generateFeaturePyramid(filePath, axes="projectedOut_y");
        self.fullVolume : np.ndarray =readPath(filePath);
        self.frameNumber : int =frameNumber;
        self.filePath : str = filePath;
        return ;

class RegProblem(NamedTuple):
    fixed: PreprocessedImgStruct ;
    moving: PreprocessedImgStruct ;
    placeToSave : str ;


def reinitialize(fixed_image, moving_image, dx, dy, angles, batch_size, device, memory_dict):
    # Note, m59htw3d8M5y2025tzET: my recollection is that this function was
    # base on git@github.com:flavell-lab/euler_gpu.git
    """
    Initialize the memory dictionary for the GNCC calculation.

    Arguments:
    - fixed_image: Fixed image, as an array of shape (H x W)
    - moving_image: Moving image, as an array of shape (H x W)
    - dx: list of translations in the x direction
    - dy: list of translations in the y direction
    - angles: list of angles to rotate the image (in degrees)
    - batch_size: number of images to process at once
    - device: PyTorch device to use (e.g. torch.device("cuda:0"))
    """

    memory_dict["transformations"] = list(itertools.product(dx, dy, angles))
    transformations = memory_dict["transformations"]

    
    # Move data to GPU
    fixed_image = torch.tensor(fixed_image, device=device, dtype=torch.float32)
    moving_image = torch.tensor(moving_image, device=device, dtype=torch.float32)

    # Repeat the image tensor to batch process
    memory_dict["moving_images_repeated"] = moving_image.unsqueeze(0).repeat(batch_size, 1, 1, 1)
    memory_dict["fixed_images_repeated"] = fixed_image.unsqueeze(0).repeat(batch_size, 1, 1, 1)

    """
    # Preallocate memory
    memory_dict["output_tensor"] = torch.zeros_like(memory_dict["moving_images_repeated"], device=device, dtype=torch.float32)
    memory_dict["grid"] = torch.zeros((batch_size, fixed_image.shape[0], fixed_image.shape[1], 2), device=device, dtype=torch.float32)
    memory_dict["gncc_results"] = torch.zeros(len(transformations), device=device, dtype=torch.float32)
    memory_dict["mu_f"] = torch.zeros((batch_size, 1, 1, 1), device=device, dtype=torch.float32)
    memory_dict["mu_m"] = torch.zeros((batch_size, 1, 1, 1), device=device, dtype=torch.float32)
    memory_dict["a"] = torch.zeros(batch_size, device=device, dtype=torch.float32)
    memory_dict["b"] = torch.zeros(batch_size, device=device, dtype=torch.float32)
    memory_dict["angles_rad"] = torch.zeros(len(transformations), device=device, dtype=torch.float32)
    memory_dict["dx_gpu"] = torch.zeros(len(transformations), device=device, dtype=torch.float32)
    memory_dict["dy_gpu"] = torch.zeros(len(transformations), device=device, dtype=torch.float32)
    memory_dict["cos_vals"] = torch.zeros(batch_size, device=device, dtype=torch.float32)
    memory_dict["sin_vals"] = torch.zeros(batch_size, device=device, dtype=torch.float32)
    memory_dict["rotation_matrices"] = torch.zeros((batch_size, 2, 3), device=device, dtype=torch.float32)
    """

    # Precompute lists of transformations to try
    for i in range(0, len(transformations), batch_size):
        max_idx = min(i+batch_size, len(transformations))
        batched_transformations = transformations[i:max_idx]

        # # Unzip the transformations
        batched_dx, batched_dy, batched_angles = zip(*batched_transformations)
        memory_dict["dx_gpu"][i:max_idx] = torch.tensor(batched_dx, device=device, dtype=torch.float32)
        memory_dict["dy_gpu"][i:max_idx] = torch.tensor(batched_dy, device=device, dtype=torch.float32)
        memory_dict["angles_rad"][i:max_idx] = (torch.tensor(batched_angles) * torch.pi / 180).to(device)

    return ;





def tryAndFindBest(im1, im2, rots, xVals, yVals, batchSize, memory_dict, DEF_DEV):
    
    if(memory_dict is None):
        memory_dict= euler_gpu.initialize(im1, im2, xVals, yVals, rots, batchSize, device=DEF_DEV);# "cuda:0")
    else:
        reinitialize(im1, im2, xVals, yVals, rots, batchSize, device=DEF_DEV, memory_dict=memory_dict);
    best_score_xy, (best_dx, best_dy, best_angle) = euler_gpu.grid_search(memory_dict)
    
    return ( best_score_xy, best_angle, best_dx, best_dy, memory_dict); 



def euclidAlign(regProblem : RegProblem, memoryDictsForLevel, DEF_DEV, logFile_fh):
    pyramidLevels=list(zip(regProblem.fixed.no_z, regProblem.moving.no_z));

    startR=0.0;
    X=0.0;
    Y=0.0;
    gncc=0.0;

    for l in range(1,len(pyramidLevels)+1):
        memory_dict_thisLevel=memoryDictsForLevel[l];
        # TODO: make the below parameters determining sampling density configurable from a file.
        (gnccSqrt, nextR_rad, X,Y, memory_dict_thisLevel) = tryAndFindBest(pyramidLevels[-l][0], pyramidLevels[-l][1], 
                ( startR + (1.5**(-l+1)) * torch.linspace(-180,180,13,dtype=torch.float64).to(DEF_DEV)) % 360,
                X+ 2 * (2 ** (-l+1) ) * torch.linspace(-1, 1,13,dtype=torch.float64).to(DEF_DEV), 
                Y+ 2 * (2 ** (-l+1) ) * torch.linspace(-1,1, 13,dtype=torch.float64).to(DEF_DEV),  
                13**3, memory_dict_thisLevel, DEF_DEV );
        # assert( ( (startR <= 2*torch.pi) and (startR >= -2*torch.pi)) or np.isclose(startR, 2 * torch.pi) or np.isclose(startR, -2 * torch.pi) );
        nextR_rad = nextR_rad % (2 * torch.pi);
        startR= np.rad2deg(nextR_rad); #(180 * startR)/torch.pi;
        assert( ( (startR <= 360) and (startR >= 0)) or np.isclose(startR, 360) or np.isclose(startR, 0) );

        memoryDictsForLevel[l]=memory_dict_thisLevel;
    
    ### incorrect - X can be outside this range, since X=1 just corresponds to half-frame shift, and similar for X=-1; considering the role of rotation and the uneven size of frame makes it worse. # assert( (X >= -1 and X <=1) or np.isclose(X, -1) or np.isclose(X,1)  );
    ### incorrect for a similar reason as the line about X above#  assert( (Y >= -1 and Y <=1) or np.isclose(Y, -1) or np.isclose(Y,1)  );

    # return (gnccSqrt, startR*(torch.pi/180), X* pyramidLevels[0][0].shape[0],Y * pyramidLevels[0][0].shape[1], (X, Y, startR*(torch.pi/180)))
    print("xy:"+str(  {"fixed#":regProblem.fixed.frameNumber, "moving#":regProblem.moving.frameNumber,"gnccSqrtOn1/4thSize":gnccSqrt, "X":X, "Y":Y, "r_rad": nextR_rad} ), file=logFile_fh); 
    assert(np.isclose(nextR_rad, np.deg2rad(startR)));
    return (X, Y, nextR_rad); # startR*(torch.pi/180));









def euclidAlign_Z(frameNumber_fixed, frameNumber_moving, inputVal, memoryDictsForLevel, DEF_DEV, logFile_fh):
    pyramidLevels=list(zip(*inputVal));

    startR=0;
    X=0;
    Y=0;
    gncc=0;

    numPoints=pyramidLevels[-1][0].shape[1] +1;
    for l in range(1,len(pyramidLevels)+1):
        memory_dict_thisLevel=memoryDictsForLevel[l];
        (gnccSqrt, startR, X,Y, memory_dict_thisLevel) = tryAndFindBest(pyramidLevels[-l][0], pyramidLevels[-l][1], 
                torch.zeros(1), 
                torch.zeros(1), 
                Y + (2 ** (-l+1) ) * torch.concat([torch.zeros(1), torch.linspace(-2,2,numPoints)]),
                numPoints, memory_dict_thisLevel, DEF_DEV );
        memoryDictsForLevel[l]=memory_dict_thisLevel;

    print("xz:"+str(  {"fixed#": frameNumber_fixed, "moving#": frameNumber_moving,"gnccSqrtOn1/4thSize":gnccSqrt, "Y":Y} ), file=logFile_fh); 
    # return (gnccSqrt, startR*(torch.pi/180), X* pyramidLevels[0][0].shape[0],Y * pyramidLevels[0][0].shape[1], (X, Y, startR*(torch.pi/180)))
    return (0, Y, 0); # Y, startR*(torch.pi/180));


"""

# Returns
- `outcomes::Dict`: A dictionary containing registration metrics and best transformation parameters, including:
  - `"registered_image_xyz_gncc_0"`: Initial GNCC score before registration.
  - `"registered_image_xyz_gncc_xy"`: GNCC score after XY-plane registration.
  - `"registered_image_xyz_gncc_xz"`: GNCC score after XZ-plane registration.
  - `"best_transformation_xy"`: Best transformation parameters for the XY plane.
  - `"best_transformation_xz"`: Best transformation parameters for the XZ plane.
  gncc fullsized fixed with fullsized transformed moving
- `transformed_moving_image_xyz::Array`: The moving image transformed to align with the fixed image.

"""


def get_downsampleRatio():
    return 2;

def getProjectionAndDownsampleFunt(vol,dim):
    downsampleRatio=get_downsampleRatio();
    if(downsampleRatio ==1):
        return torch.max(vol, dim=dim);  
    else:
        return euler_gpu.max_intensity_projection_and_downsample(vol, downsampleRatio, projection_axis=dim);


def handlerEuclidAlign(valuesToProcess, lineLeaderString, DEF_DEV, logFile_fh):
    results=[];
    memoryDictsForLevel_xy=[None, None, None, None, None, None, None, None];
    memoryDictsForLevel_xz=[None, None, None, None, None, None, None, None];
    for thisRegProblem in valuesToProcess:
        solutionToRegProblem=dict();
        results.append(solutionToRegProblem);

        solutionToRegProblem["best_transformation_xy"] = euclidAlign(thisRegProblem, memoryDictsForLevel_xy, DEF_DEV, logFile_fh);
        fullVolume_xy_shape=thisRegProblem.fixed.fullVolume.shape[:2];
        fullVolume_z_shape=thisRegProblem.moving.fullVolume.shape[2];
        _memory_dict_xy = euler_gpu.initialize(
            torch.zeros(fullVolume_xy_shape),
            torch.zeros(fullVolume_xy_shape),
            torch.zeros(fullVolume_z_shape),
            torch.zeros(fullVolume_z_shape),
            torch.zeros(fullVolume_z_shape),
            fullVolume_z_shape,
            DEF_DEV
        )

        transformed_moving_image_xyz = euler_gpu.transform_image_3d(
            thisRegProblem.moving.fullVolume,
            _memory_dict_xy,
            solutionToRegProblem["best_transformation_xy"] ,
            DEF_DEV,
            2
            )

        downSampled_transformed_moving_image_xyz= getProjectionAndDownsampleFunt(transformed_moving_image_xyz, dim=1); # euler_gpu.max_intensity_projection_and_downsample(transformed_moving_image_xyz, 2, projection_axis=1);
        pyrRotatedMoving=[x for x in pyramid_gaussian(downSampled_transformed_moving_image_xyz) if (min(x.shape) >= 4) ];
        
        solutionToRegProblem["best_transformation_xz"] = euclidAlign_Z(\
            thisRegProblem.fixed.frameNumber, \
            thisRegProblem.moving.frameNumber, \
            [thisRegProblem.fixed.no_y, pyrRotatedMoving], memoryDictsForLevel_xz, DEF_DEV, logFile_fh);

        zTransform=solutionToRegProblem["best_transformation_xz"][1];
        finalTransformedImg= translate_z(transformed_moving_image_xyz,  -int(np.round(zTransform * transformed_moving_image_xyz.shape[2]) / 2), 0.0)

        nrrd.write(thisRegProblem.placeToSave, finalTransformedImg);

        # downSampled_transformed_moving_image_xz = euler_gpu.max_intensity_projection_and_downsample(finalTransformedImg, 4, projection_axis=1); 
        # solutionToRegProblem["transformed_moving_volume"] = downSampled_transformed_moving_image_xz;
        solutionToRegProblem["placeFinalVolumeSaved"] = thisRegProblem.placeToSave ; 
        ########### solutionToRegProblem["finalTransformedImg"]=finalTransformedImg;
        for keyName, val in [ ("fixed", thisRegProblem.fixed), ("moving", thisRegProblem.moving) ]:
           solutionToRegProblem[keyName] = {"path": val.filePath , "indx": val.frameNumber };



    return results;



#V~V~V~V~V~V~V~V~V~V~V~V~V~V~V~V~V~V~V~V~V~V~V~V~V
# From Euler GPU:
# git@github.com:flavell-lab/euler_gpu.git
# commit b7ada1272017d52e68e69e25cf5fd5c891b06298
# file: gncc.py
# lines 43 to 50, inclusive of both  
#=================================================


def calculate_gncc(fixed, moving, epsForStability=0): # 1e-8):
    # print("cgf:"+str(fixed)[:1000]);
    # print("cgm:"+str(moving)[:1000]);
    mu_f = np.mean(fixed)
    mu_m = np.mean(moving)
    a = np.sum((fixed - mu_f) * (moving - mu_m))
    b = np.sqrt(np.sum((fixed - mu_f) ** 2) * np.sum((moving - mu_m) ** 2)+epsForStability)

    return a / b

# Below was originally written in Julia - it has been translated to Python....
# TODO: check the Julia versus Python array indices....
def translate_z(image, shift, fill_value):
    # Get the size of the image
    dims = image.shape

    # Create a new array to hold the translated image
    translated_image = fill_value * np.ones(dims)

    if(shift > 0):
        translated_image[:, :, (shift):(dims[2])] = image[:, :, 0:(dims[2]-shift)]
    else:
        translated_image[:, :, 0:(dims[2]+shift)] = image[:, :, (-shift):(dims[2])]

    return translated_image




#^_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^^_^_^


def readPath(path):
    return nrrd.read(path)[0];

def readAndGiveMIP(path, axes):
    if(axes not in ["projectedOut_z", "projectedOut_y"]):
        raise Exception("Axes unknown, "+str(axes));
    dim=2;
    if(axes=="projectedOut_y"):
        dim=1;
    initialNrrd=readPath(path);
    # return torch.max(initialNrrd, dim=dim);    #  euler_gpu.max_intensity_projection_and_downsample(initialNrrd, 4, projection_axis=dim); 
    return getProjectionAndDownsampleFunt(initialNrrd, dim=dim); # euler_gpu.max_intensity_projection_and_downsample(initialNrrd, 2, projection_axis=dim);


def generateFeaturePyramid(img1, axes):
    return [x for x in pyramid_gaussian(readAndGiveMIP(img1, axes)) if (min(x.shape) >= 4) ];


def getDistributionORegProblemsOverProcesses(k,m,initialRegProblemsSpec: List[Tuple[Tuple[str,int], Tuple[str,int], str]] ) -> List[Tuple[Tuple[str,int], Tuple[str,int], str]]  :
    contentRead : List[Tuple[Tuple[str,int], Tuple[str,int], str]] =[ x for indx, x in enumerate(initialRegProblemsSpec) if ( (indx // (len(initialRegProblemsSpec) /k) ) == m ) ];
    return contentRead;
    

def getExecutionOrderAcrossProcesses(k,initialRegProblemsSpec):
    problemByExecutionOrder=[];
    for m in range(0,k):
        for thisIndx, thisProblem in enumerate(getDistributionORegProblemsOverProcesses(k,m,initialRegProblemsSpec)):
            if(thisIndx >= len(problemByExecutionOrder)):
                problemByExecutionOrder.append([]);
            problemByExecutionOrder[thisIndx].append(thisProblem);
    return problemByExecutionOrder;
            


def readRegProblems(k,m,initialRegProblemsSpec: List[Tuple[Tuple[str,int], Tuple[str,int], str]] ) -> List[RegProblem] : 
    # Below line selects the subset of records that this process does on to address.
    # The indexing in the conditional is done so that it is easier to pass the values to take 
    # advantage of memory saving etc.
    contentRead : List[Tuple[Tuple[str,int], Tuple[str,int], str]] =getDistributionORegProblemsOverProcesses(k,m,initialRegProblemsSpec); 
    
    listOfImagesToRead : List[Tuple[str,int]]=list(set([ w2 for w in contentRead for w2 in w[:2] ]));
    dictMappingPathToImg : Dict[Tuple[str,int], PreprocessedImgStruct] ={ \
        (name,num) : PreprocessedImgStruct(name, num)  \
        for name, num in listOfImagesToRead}; 
    
    preProcessedRegProblems : List[RegProblem] =[  RegProblem(fixed= dictMappingPathToImg[w[0]], \
                              moving=dictMappingPathToImg[w[1]], placeToSave=w[2]) \
        for w in contentRead ]
    
    return preProcessedRegProblems;


import traceback;

def main_helper(tupleValInput):
    m,k,contentRead, placeToSaveBase = tupleValInput ;
    logFile_fh=open(f"{placeToSaveBase}log_{m}of{k}.txt", "w");
    # t2=time.time();

    # We set the environment variables inside the processes
    # just to be sure those settings are in effected for the
    # duplicated threads etc.
    for (thisKey,thisVal) in [ ("MKL_NUM_THREADS", "2"), 
                   ("NUMEXPR_NUM_THREADS", "2"),
                   ("OMP_NUM_THREADS", "2")]:
        os.environ[thisKey] = thisVal;

    if(m >= k):
        raise Exception("Invalid value of k and m");

    
    # TODO: assign CPUs in order of ascending percent use, instead of
    # just blindly assigning a number or random selection (which for the number of
    # threads we intend to use would likely still result in tasks being assigned to 
    # particularly busy CPUs or so forth).
    DEF_DEV="cpu:"+str(m);
    torch.set_default_device(DEF_DEV);
    torch.set_num_threads(2); # we have two thread contexts per CPU

    
    try:
        valToReturn=handlerEuclidAlign(readRegProblems(k,m,contentRead), str((k,m)), DEF_DEV, logFile_fh);
    except Exception as e:
        logFile_fh.flush();
        print(traceback.format_exc().replace("\n", "\n    "), flush=True, file=logFile_fh);
        logFile_fh.close();
        raise e;

    logFile_fh.flush();
    logFile_fh.close();

    # t3=time.time();
    # print( str((k,m))+ ": Done computing Euclidean registration:" + str(t3) + ", time elapsed:"+str(t3-t2), flush=True);
    ## to the left would be wrong type... ### valToReturn["compute_time_info"] = (t2,t3,k,m);
    return valToReturn;


import time; 

def main(k, contentRead, placeToSaveLogsBase=None):
    results=[];

    if(placeToSaveLogsBase is None):
        placeToSaveLogsBase="./processLogs_eulerReg_"+str(time.time()) + "/";
        os.makedirs(placeToSaveLogsBase);

    arguments=[ (m,k,contentRead, placeToSaveLogsBase) for m in range(k) ];
    with Pool(k) as p:
        # results = p.map( localFunct  , list(range(k)))
        results= p.map( main_helper, arguments);


    assert(len(results) == k);
    valToReturn=[];
    for subList in results:
        valToReturn.extend(subList);
    assert(len(valToReturn) == sum([ len(x) for x in results ]) );
    return valToReturn;

# main(1,[])

def run_test():
    main(20, [ \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0038_ch2.nrrd", 38), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0001_ch2.nrrd", 1), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/1to38/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0044_ch2.nrrd", 44), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0001_ch2.nrrd", 1), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/1to44/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0051_ch2.nrrd", 51), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0001_ch2.nrrd", 1), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/1to51/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0081_ch2.nrrd", 81), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0001_ch2.nrrd", 1), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/1to81/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0175_ch2.nrrd", 175), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0001_ch2.nrrd", 1), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/1to175/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0228_ch2.nrrd", 228), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0001_ch2.nrrd", 1), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/1to228/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0584_ch2.nrrd", 584), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0001_ch2.nrrd", 1), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/1to584/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0602_ch2.nrrd", 602), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0001_ch2.nrrd", 1), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/1to602/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0636_ch2.nrrd", 636), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0001_ch2.nrrd", 1), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/1to636/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0679_ch2.nrrd", 679), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0001_ch2.nrrd", 1), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/1to679/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t1196_ch2.nrrd", 1196), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0001_ch2.nrrd", 1), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/1to1196/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t1406_ch2.nrrd", 1406), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0001_ch2.nrrd", 1), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/1to1406/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0098_ch2.nrrd", 98), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0002_ch2.nrrd", 2), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/2to98/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0100_ch2.nrrd", 100), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0002_ch2.nrrd", 2), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/2to100/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0173_ch2.nrrd", 173), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0002_ch2.nrrd", 2), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/2to173/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0263_ch2.nrrd", 263), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0002_ch2.nrrd", 2), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/2to263/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0367_ch2.nrrd", 367), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0002_ch2.nrrd", 2), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/2to367/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0402_ch2.nrrd", 402), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0002_ch2.nrrd", 2), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/2to402/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0514_ch2.nrrd", 514), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0002_ch2.nrrd", 2), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/2to514/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0549_ch2.nrrd", 549), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0002_ch2.nrrd", 2), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/2to549/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0597_ch2.nrrd", 597), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0002_ch2.nrrd", 2), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/2to597/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0700_ch2.nrrd", 700), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0002_ch2.nrrd", 2), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/2to700/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0711_ch2.nrrd", 711), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0002_ch2.nrrd", 2), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/2to711/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0798_ch2.nrrd", 798), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0002_ch2.nrrd", 2), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/2to798/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t1334_ch2.nrrd", 1334), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0002_ch2.nrrd", 2), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/2to1334/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t1533_ch2.nrrd", 1533), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0002_ch2.nrrd", 2), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/2to1533/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0021_ch2.nrrd", 21), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0003_ch2.nrrd", 3), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/3to21/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0046_ch2.nrrd", 46), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0003_ch2.nrrd", 3), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/3to46/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0070_ch2.nrrd", 70), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0003_ch2.nrrd", 3), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/3to70/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0095_ch2.nrrd", 95), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0003_ch2.nrrd", 3), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/3to95/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0116_ch2.nrrd", 116), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0003_ch2.nrrd", 3), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/3to116/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0157_ch2.nrrd", 157), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0003_ch2.nrrd", 3), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/3to157/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0216_ch2.nrrd", 216), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0003_ch2.nrrd", 3), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/3to216/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0278_ch2.nrrd", 278), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0003_ch2.nrrd", 3), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/3to278/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0330_ch2.nrrd", 330), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0003_ch2.nrrd", 3), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/3to330/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0340_ch2.nrrd", 340), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0003_ch2.nrrd", 3), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/3to340/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0368_ch2.nrrd", 368), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0003_ch2.nrrd", 3), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/3to368/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0372_ch2.nrrd", 372), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0003_ch2.nrrd", 3), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/3to372/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0440_ch2.nrrd", 440), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0003_ch2.nrrd", 3), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/3to440/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0473_ch2.nrrd", 473), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0003_ch2.nrrd", 3), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/3to473/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0516_ch2.nrrd", 516), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0003_ch2.nrrd", 3), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/3to516/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0603_ch2.nrrd", 603), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0003_ch2.nrrd", 3), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/3to603/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0737_ch2.nrrd", 737), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0003_ch2.nrrd", 3), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/3to737/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0775_ch2.nrrd", 775), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0003_ch2.nrrd", 3), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/3to775/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t1384_ch2.nrrd", 1384), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0003_ch2.nrrd", 3), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/3to1384/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t1418_ch2.nrrd", 1418), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0003_ch2.nrrd", 3), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/3to1418/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t1472_ch2.nrrd", 1472), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0003_ch2.nrrd", 3), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/3to1472/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0025_ch2.nrrd", 25), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0004_ch2.nrrd", 4), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/4to25/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0034_ch2.nrrd", 34), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0004_ch2.nrrd", 4), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/4to34/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0090_ch2.nrrd", 90), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0004_ch2.nrrd", 4), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/4to90/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0174_ch2.nrrd", 174), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0004_ch2.nrrd", 4), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/4to174/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0179_ch2.nrrd", 179), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0004_ch2.nrrd", 4), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/4to179/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0308_ch2.nrrd", 308), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0004_ch2.nrrd", 4), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/4to308/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0416_ch2.nrrd", 416), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0004_ch2.nrrd", 4), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/4to416/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0417_ch2.nrrd", 417), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0004_ch2.nrrd", 4), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/4to417/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0477_ch2.nrrd", 477), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0004_ch2.nrrd", 4), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/4to477/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0501_ch2.nrrd", 501), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0004_ch2.nrrd", 4), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/4to501/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0536_ch2.nrrd", 536), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0004_ch2.nrrd", 4), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/4to536/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0589_ch2.nrrd", 589), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0004_ch2.nrrd", 4), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/4to589/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0669_ch2.nrrd", 669), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0004_ch2.nrrd", 4), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/4to669/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0695_ch2.nrrd", 695), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0004_ch2.nrrd", 4), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/4to695/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0705_ch2.nrrd", 705), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0004_ch2.nrrd", 4), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/4to705/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t1010_ch2.nrrd", 1010), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0004_ch2.nrrd", 4), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/4to1010/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t1104_ch2.nrrd", 1104), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0004_ch2.nrrd", 4), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/4to1104/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t1105_ch2.nrrd", 1105), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0004_ch2.nrrd", 4), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/4to1105/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t1443_ch2.nrrd", 1443), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0004_ch2.nrrd", 4), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/4to1443/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t1447_ch2.nrrd", 1447), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0004_ch2.nrrd", 4), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/4to1447/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0233_ch2.nrrd", 233), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0005_ch2.nrrd", 5), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/5to233/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0243_ch2.nrrd", 243), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0005_ch2.nrrd", 5), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/5to243/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0281_ch2.nrrd", 281), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0005_ch2.nrrd", 5), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/5to281/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0406_ch2.nrrd", 406), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0005_ch2.nrrd", 5), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/5to406/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0429_ch2.nrrd", 429), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0005_ch2.nrrd", 5), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/5to429/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0474_ch2.nrrd", 474), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0005_ch2.nrrd", 5), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/5to474/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0485_ch2.nrrd", 485), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0005_ch2.nrrd", 5), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/5to485/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0543_ch2.nrrd", 543), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0005_ch2.nrrd", 5), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/5to543/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0563_ch2.nrrd", 563), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0005_ch2.nrrd", 5), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/5to563/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0599_ch2.nrrd", 599), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0005_ch2.nrrd", 5), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/5to599/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0616_ch2.nrrd", 616), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0005_ch2.nrrd", 5), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/5to616/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0700_ch2.nrrd", 700), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0005_ch2.nrrd", 5), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/5to700/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0703_ch2.nrrd", 703), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0005_ch2.nrrd", 5), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/5to703/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0781_ch2.nrrd", 781), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0005_ch2.nrrd", 5), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/5to781/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t1201_ch2.nrrd", 1201), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0005_ch2.nrrd", 5), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/5to1201/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t1206_ch2.nrrd", 1206), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0005_ch2.nrrd", 5), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/5to1206/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t1209_ch2.nrrd", 1209), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0005_ch2.nrrd", 5), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/5to1209/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t1298_ch2.nrrd", 1298), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0005_ch2.nrrd", 5), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/5to1298/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t1564_ch2.nrrd", 1564), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0005_ch2.nrrd", 5), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/5to1564/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0096_ch2.nrrd", 96), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0006_ch2.nrrd", 6), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/6to96/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0205_ch2.nrrd", 205), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0006_ch2.nrrd", 6), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/6to205/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0235_ch2.nrrd", 235), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0006_ch2.nrrd", 6), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/6to235/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0282_ch2.nrrd", 282), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0006_ch2.nrrd", 6), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/6to282/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0350_ch2.nrrd", 350), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0006_ch2.nrrd", 6), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/6to350/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0355_ch2.nrrd", 355), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0006_ch2.nrrd", 6), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/6to355/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0358_ch2.nrrd", 358), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0006_ch2.nrrd", 6), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/6to358/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0487_ch2.nrrd", 487), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0006_ch2.nrrd", 6), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/6to487/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0561_ch2.nrrd", 561), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0006_ch2.nrrd", 6), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/6to561/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0741_ch2.nrrd", 741), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0006_ch2.nrrd", 6), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/6to741/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t1078_ch2.nrrd", 1078), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0006_ch2.nrrd", 6), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/6to1078/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t1156_ch2.nrrd", 1156), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0006_ch2.nrrd", 6), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/6to1156/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t1297_ch2.nrrd", 1297), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0006_ch2.nrrd", 6), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/6to1297/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t1323_ch2.nrrd", 1323), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0006_ch2.nrrd", 6), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/6to1323/euler_transformed.nrrd"), \
    (("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t1449_ch2.nrrd", 1449), ("/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/2025-02-19-01_t0006_ch2.nrrd", 6), "/store1/david/euler_reg_d22M2y2025tzET/data/newEuler_s39m35htw22d23M03y2025tzMDT/6to1449/euler_transformed.nrrd") \
    ]);
