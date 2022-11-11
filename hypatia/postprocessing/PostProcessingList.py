from hypatia.postprocessing.DefaultPostProcessing import DefaultPostProcessing
from hypatia.postprocessing.Italy2020PostProcessing import Italy2020PostProcessing

POSTPROCESSING_MODULES = {
    "default": DefaultPostProcessing,
    "it2020": Italy2020PostProcessing,
}
