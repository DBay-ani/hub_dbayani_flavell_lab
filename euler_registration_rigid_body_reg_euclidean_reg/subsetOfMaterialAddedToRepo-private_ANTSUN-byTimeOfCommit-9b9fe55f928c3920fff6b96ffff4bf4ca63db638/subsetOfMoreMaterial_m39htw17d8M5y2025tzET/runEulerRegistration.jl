#VV~V~V~V~V~V~V~V~V~~V~V~V~V~V~V~V~VV~~V~V~V~VV~~V~V
# Copied from the Julia notebook
##===================================================

#V~V~V~V~V~V~V~V~V~V~V~V~~V~V~V~V~V~V~V~V~V~V~VV~V~V
# Initial imports in the notebook
##==================================================

# Flavell lab packages
using ND2Process
using GPUFilter
using WormFeatureDetector
using NRRDIO
using FlavellBase
using SegmentationTools
using ImageDataIO
using RegistrationGraph
using ExtractRegisteredData
using CaAnalysis
using BehaviorDataNIR
using UNet2D
using ImageRegistration

# Other packages
using ProgressMeter
using PyCall
using PyPlot
using Statistics
using StatsBase
using DelimitedFiles
using Images
using Cairo
using Distributions
using DataStructures
using HDF5
using Interact
using WebIO
using Plots
# using GraphPlot
# using LightGraphs
# using SimpleWeightedGraphs
using Dates
using JLD2
using TotalVariation
using VideoIO
using Distributions
using MultivariateStats
using FFTW
using LinearAlgebra
using GLMNet
using InformationMeasures
using CUDA
using LsqFit
using Optim
using Rotations
using CoordinateTransformations
using ImageTransformations
using Interpolations
using H5Zblosc

using Distributed
#_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^


#V~V~V~V~V~V~V~V~~V~V~V~V~~V~V~V~~V~V~V~V
# From sections later  in the notebook but still before first
# Euler registration
##=======================================
using ImageDataIO
using PyCall
using NRRDIO
using Statistics
import JLD2
#_^_^_^__^_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^


#_^_^_^__^_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^_^


