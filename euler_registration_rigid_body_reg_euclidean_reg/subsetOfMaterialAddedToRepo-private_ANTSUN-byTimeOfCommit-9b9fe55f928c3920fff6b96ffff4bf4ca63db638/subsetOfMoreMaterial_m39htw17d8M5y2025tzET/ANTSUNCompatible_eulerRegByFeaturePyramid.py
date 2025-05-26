import cv2;
import nrrd; 

# from multiprocessing import Pool

import itertools;

import matplotlib.pyplot as plt;

from PIL import Image
import numpy as np;
# import imreg_dft as ird;

import cv2;

import nrrd;
# import imutils;

# import euler_gpu

import skimage as ski; 


import euler_gpu; 


def reinitialize(fixed_image, moving_image, dx, dy, angles, batch_size, device, memory_dict):
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





def tryAndFindBest(im1, im2, rots, xVals, yVals, batchSize, memory_dict):
    
    if(memory_dict is None):
        memory_dict= euler_gpu.initialize(im1, im2, xVals, yVals, rots, batchSize, device=DEF_DEV);# "cuda:0")
    else:
        reinitialize(im1, im2, xVals, yVals, rots, batchSize, device=DEF_DEV, memory_dict=memory_dict);
    best_score_xy, (best_dx, best_dy, best_angle) = euler_gpu.grid_search(memory_dict)
    
    return ( best_score_xy, best_angle, best_dx, best_dy, memory_dict); 

from skimage.transform import pyramid_gaussian
import torch; 


import time;
def euclidAlign(inputVal, memoryDictsForLevel):
    pyramidLevels=list(zip(*inputVal));

    startR=0;
    X=0;
    Y=0;
    gncc=0;

    for l in range(1,len(pyramidLevels)+1):
        memory_dict_thisLevel=memoryDictsForLevel[l];
        (gnccSqrt, startR, X,Y, memory_dict_thisLevel) = tryAndFindBest(pyramidLevels[-l][0], pyramidLevels[-l][1], 
                startR + (1.5**(-l+1)) * torch.linspace(-180,180,13,dtype=torch.float64).to(DEF_DEV),
                X+ 2 * (2 ** (-l+1) ) * torch.linspace(-1, 1,13,dtype=torch.float64).to(DEF_DEV), 
                Y+ 2 * (2 ** (-l+1) ) * torch.linspace(-1,1, 13,dtype=torch.float64).to(DEF_DEV),  
                13**3, memory_dict_thisLevel );
        startR= (180 * startR)/torch.pi;
        memoryDictsForLevel[l]=memory_dict_thisLevel;
        
    return (gnccSqrt, startR*(torch.pi/180), X* pyramidLevels[0][0].shape[0],Y * pyramidLevels[0][0].shape[1], (X, Y, startR*(torch.pi/180)))










def euclidAlign_Z(inputVal, memoryDictsForLevel):
    pyramidLevels=list(zip(*inputVal));

    startR=0;
    X=0;
    Y=0;
    gncc=0;

    numPoints=pyramidLevels[-1][0].shape[1] +1;
    for l in range(1,len(pyramidLevels)+1):
        ### print(".");
        memory_dict_thisLevel=memoryDictsForLevel[l];
        (gnccSqrt, startR, X,Y, memory_dict_thisLevel) = tryAndFindBest(pyramidLevels[-l][0], pyramidLevels[-l][1], 
                torch.zeros(1), 
                torch.zeros(1), 
                Y + (2 ** (-l+1) ) * torch.concat([torch.zeros(1), torch.linspace(-2,2,numPoints)]),
                numPoints, memory_dict_thisLevel );
        memoryDictsForLevel[l]=memory_dict_thisLevel;
        
    return (gnccSqrt, startR*(torch.pi/180), X* pyramidLevels[0][0].shape[0],Y * pyramidLevels[0][0].shape[1], (X, Y, startR*(torch.pi/180)))



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



from euler_gpu.transform import transform_image ; 

def handlerEuclidAlign(valuesToProcess, lineLeaderString):
    results=[];
    memoryDictsForLevel_xy=[None, None, None, None, None, None, None, None];
    memoryDictsForLevel_xz=[None, None, None, None, None, None, None, None];
    for thisValInitial in valuesToProcess:
        thisVal = [x[0]["z"] for x in thisValInitial];
        results.append([]);
        results[-1].append(euclidAlign(thisVal, memoryDictsForLevel_xy));
        _memory_dict_xy = euler_gpu.initialize(
            torch.zeros(thisValInitial[0][0][0][:,:,1].shape),
            torch.zeros(thisValInitial[1][0][0][:,:,1].shape),
            torch.zeros(thisValInitial[1][0][0].shape[2]),
            torch.zeros(thisValInitial[1][0][0].shape[2]),
            torch.zeros(thisValInitial[1][0][0].shape[2]),
            thisValInitial[1][0][0].shape[2],
            DEF_DEV
        )

        AAA=thisValInitial[0][0]["z"][0]
        BBB = thisValInitial[1][0]["z"][0]

        transformed_moving_image_xyz = euler_gpu.transform_image_3d(
            thisValInitial[1][0][0],
            _memory_dict_xy,
            results[-1][0][-1] ,
            DEF_DEV,
            2
            )

        CCC = euler_gpu.max_intensity_projection_and_downsample(transformed_moving_image_xyz, 4, projection_axis=2);

        DDD= transform_image(
                torch.tensor(thisVal[1][0], dtype=torch.float32, device=DEF_DEV).expand(1,1,thisVal[1][0].shape[0],thisVal[1][0].shape[1]),
                    results[-1][0][-1][0] * torch.ones(1,dtype=torch.float32),
                    results[-1][0][-1][1] * torch.ones(1,dtype=torch.float32),
                    results[-1][0][-1][2] * torch.ones(1,dtype=torch.float32),
                    euler_gpu.initialize(torch.tensor(thisVal[1][0], dtype=torch.float32, device=DEF_DEV),\
                                         torch.tensor(thisVal[1][0], dtype=torch.float32, device=DEF_DEV),\
                            torch.ones(1,dtype=torch.float32), torch.ones(1,dtype=torch.float32), torch.ones(1,dtype=torch.float32), 1, device=DEF_DEV) 
                    );
                    # memoryDictsForLevel_xy[0]);

        #print(str(thisValInitial[1][0][0].shape),flush=True);
        #print(str(thisVal[1][0].shape), flush=True);
        # continue
 
        """
        EEE= transform_image(
                torch.tensor(np.max(thisValInitial[1][0][0],axis=2) , dtype=torch.float32, device=DEF_DEV).expand(1,1,thisVal[1][0].shape[0],thisVal[1][0].shape[1]),
                    results[-1][0][-1][0] * torch.ones(1,dtype=torch.float32),
                    results[-1][0][-1][1] * torch.ones(1,dtype=torch.float32),
                    results[-1][0][-1][2] * torch.ones(1,dtype=torch.float32),
                    euler_gpu.initialize(torch.tensor(thisVal[1][0], dtype=torch.float32, device=DEF_DEV),\
                                         torch.tensor(thisVal[1][0], dtype=torch.float32, device=DEF_DEV),\
                            torch.ones(1,dtype=torch.float32), torch.ones(1,dtype=torch.float32), torch.ones(1,dtype=torch.float32), 1, device=DEF_DEV)
                    );
        """
        # print(str(DDD.reshape(AAA.shape))[:1000],flush=True);
        #####temp_write_22fbc2be-1e8f-4d0b-9f22-6c8b51e34089####print("original gncc, 3d v 3d:"+str(calculate_gncc(thisValInitial[0][0][0], thisValInitial[1][0][0])), flush=True);
        #####temp_write_22fbc2be-1e8f-4d0b-9f22-6c8b51e34089####print("original gncc, xy projections:"+str(calculate_gncc( AAA, CCC)), flush=True);
        #####temp_write_22fbc2be-1e8f-4d0b-9f22-6c8b51e34089####print("gncc of xy projections  after adjusting xy:"+str(calculate_gncc( AAA, np.array(DDD.reshape(AAA.shape)))), flush=True);
        #####temp_write_22fbc2be-1e8f-4d0b-9f22-6c8b51e34089####print("gncc of the 3d volumes after adjusting the xy:"+str(calculate_gncc(thisValInitial[0][0][0], transformed_moving_image_xyz)), flush=True); 

        #####temp_write_22fbc2be-1e8f-4d0b-9f22-6c8b51e34089####im=Image.fromarray(np.concatenate((AAA,BBB,CCC,DDD.reshape(AAA.shape)), axis=1)).convert('RGB');
        #####temp_write_22fbc2be-1e8f-4d0b-9f22-6c8b51e34089####im.save( "temp_xy"+ ("_".join([str(x[2]) for x in thisValInitial]))    +".png");
        #continue;

        # print("\n-----");
        downSampled_transformed_moving_image_xyz= euler_gpu.max_intensity_projection_and_downsample(transformed_moving_image_xyz, 4, projection_axis=1);
        # print("CONFIRM:xy:"+str( calculate_gncc(thisValInitial[0][0]["z"][0],euler_gpu.max_intensity_projection_and_downsample(transformed_moving_image_xyz, 4, projection_axis=2))),flush=True);
        # print("CONFIRM:xz:"+str( calculate_gncc(thisValInitial[0][0]["y"][0],euler_gpu.max_intensity_projection_and_downsample(transformed_moving_image_xyz, 4, projection_axis=1))),flush=True);

        pyrRotatedMoving=[x for x in pyramid_gaussian(downSampled_transformed_moving_image_xyz) if (min(x.shape) >= 4) ];
        
        results[-1].append(euclidAlign_Z([thisValInitial[0][0]["y"], pyrRotatedMoving], memoryDictsForLevel_xz));
        ##################### print(lineLeaderString+":" + str([www for www in zip(results[-1], ["xy","xz"])] ),flush=True);

        placeToSave="/scratch/david/euler_reg_s48m17htw19d11M03y2025tzUTC";
        zTransform=results[-1][-1][-1][1];
        finalTransformedImg= translate_z(transformed_moving_image_xyz,  -int(np.round(zTransform * transformed_moving_image_xyz.shape[2]) / 2), 0.0)

        downSampled_transformed_moving_image_xz = euler_gpu.max_intensity_projection_and_downsample(finalTransformedImg, 4, projection_axis=1); 

        ### print(str(calculate_gncc( AAA, CCC)), flush=True);
        #####temp_write_22fbc2be-1e8f-4d0b-9f22-6c8b51e34089####print("Gnnc of 3d volumes after adjustement in x, y, and z"+str(calculate_gncc( thisValInitial[0][0][0], finalTransformedImg )), flush=True);
        #####temp_write_22fbc2be-1e8f-4d0b-9f22-6c8b51e34089####print("gnnc of the xz projections of the adjusted 3D volumes (e.g., after the moving volume had x, y, and z adjusted):"+str(calculate_gncc( euler_gpu.max_intensity_projection_and_downsample(thisValInitial[0][0][0], 4, projection_axis=1), downSampled_transformed_moving_image_xz)), flush=True);
        #####temp_write_22fbc2be-1e8f-4d0b-9f22-6c8b51e34089####print("GNnC of the original 3d volumes projected onto the xz plane:" + str(calculate_gncc( euler_gpu.max_intensity_projection_and_downsample(thisValInitial[0][0][0], 4, projection_axis=1), \
        #####temp_write_22fbc2be-1e8f-4d0b-9f22-6c8b51e34089####                   euler_gpu.max_intensity_projection_and_downsample(thisValInitial[1][0][0], 4, projection_axis=1) \
        #####temp_write_22fbc2be-1e8f-4d0b-9f22-6c8b51e34089####                   )) + "\n", flush=True);

        print("new:"+ str(tuple([x[2] for x in thisValInitial])) + "," + \
            str(calculate_gncc( thisValInitial[0][0][0], finalTransformedImg )) + "," + \
            str(
calculate_gncc( euler_gpu.max_intensity_projection_and_downsample(thisValInitial[0][0][0],4, projection_axis=2),
                euler_gpu.max_intensity_projection_and_downsample(finalTransformedImg,4, projection_axis=2)
                )
            )+ "," + \
            str(
                calculate_gncc( euler_gpu.max_intensity_projection_and_downsample(thisValInitial[0][0][0],4, projection_axis=1),
                    euler_gpu.max_intensity_projection_and_downsample(finalTransformedImg,4, projection_axis=1)
                )
            )
            ,\
            flush=True);


        #nrrd.write(placeToSave +"/"+ ("_".join([str(x[2]) for x in thisValInitial])) + ".nrrd", finalTransformedImg);

    return results;

print("type:(fixed,moving),gncc for 3D vol after registration,gncc for xy projection,gncc for xz projection",flush=True); 

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


import nrrd;

def readPath(path):
    return nrrd.read(path)[0];

def readAndGiveMIP(path, axes):
    if(axes not in ["z", "y"]):
        raise Exception("Axes unknown, "+str(axes));
    dim=2;
    if(axes=="y"):
        dim=1;
    initialNrrd=readPath(path);
    return euler_gpu.max_intensity_projection_and_downsample(initialNrrd, 4, projection_axis=dim); 



def generateFeaturePyramid(img1, axes):
    return [x for x in pyramid_gaussian(readAndGiveMIP(img1, axes)) if (min(x.shape) >= 4) ];


def readRegProblems(k,m):
    baseToPath="/store1/david/euler_reg_d22M2y2025tzET/data/panneuralGFP_SWF1212/2025-02-19-01_output/";
    pathToRead=baseToPath + "registrationProblems.txt";
    baseToPath="/store1/shared/panneuralGFP_SWF1212/data_processed_220/2025-02-19-01_output/NRRD_filtered/";
    fh=open(pathToRead, "r"); 
    contentRead =  [ [(baseToPath + "2025-02-19-01_t"  +f"{int(y):04d}"  + "_ch2.nrrd",y)  for y in x.split(",")] \
            for indx, x in enumerate(fh.read().split("\n")) if (len(x) > 0  and ((indx % k) == m) )];
    listOfImagesToRead=list(set([ w2 for w in contentRead for w2 in w ]));
    dictMappingPathToImg={ \
        name : { "z": generateFeaturePyramid(name, axes="z"), \
                 "y": generateFeaturePyramid(name, axes="y"), \
                 0: readPath(name)   } \
        for name, num in listOfImagesToRead}; # , tupleList)};
    contentRead=[[ (dictMappingPathToImg[w2[0]],w2[0],w2[1]) for w2 in w] for w in contentRead ]
    return contentRead;



import time;


k=10; 

t2=time.time();

import sys;
k, m =  [int(x) for x in sys.stdin.readline().split(",")];
if(m >= k):
    raise Exception("Invalid value of k and m");

DEF_DEV="cpu:"+str(m);
torch.set_default_device(DEF_DEV);
torch.set_num_threads(2); # we have two thread contexts per CPU

handlerEuclidAlign(readRegProblems(k,m), str((k,m)));


t3=time.time();
print( str((k,m))+ ": Done computing Euclidean registration:" + str(t3) + ", time elapsed:"+str(t3-t2), flush=True);

