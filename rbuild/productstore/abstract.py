#
# Copyright (c) 2008 rPath, Inc.
#
# This program is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.rpath.com/permanent/licenses/CPL-1.0.
#
# This program is distributed in the hope that it will be useful, but
# without any warranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
#
import os

from rpath_common.proddef import api1 as proddef

from rbuild import errors
from rbuild.internal.internal_types import WeakReference


# "Method could be a function"
# Since this is a base class, methods here might look like they could
# be functions, but really need to be methods in subclasses
#pylint: disable-msg=R0201

class ProductStore(object):
    """
    Base product store class, containing methods common to all product
    stores.
    """

    # Transparently weak-reference our handle so no dependency loop is
    # created.
    _handle = WeakReference()

    def __init__(self, handle=None):
        self._handle = handle
        self._currentStage = None

    def setHandle(self, handle):
        self._handle = handle

    def getProduct(self):
        return proddef.ProductDefinition()

    def update(self):
        """
        This is the only acceptable way to update a product definition
        because it invalidates any cached copy of the data.
        """
        self._handle.product = self.getProduct()

    def iterStageNames(self):
        return (x.name for x in self._handle.product.getStages())

    def getNextStageName(self, stageName):
        stageNames = list(self.iterStageNames())
        stageIdx = stageNames.index(stageName)
        if stageIdx + 1 == len(stageNames):
            return None
        return stageNames[stageIdx + 1]

    def getActiveStageName(self):
        if self._currentStage is None:
            raise errors.RbuildError('No current stage (setActiveStageName)')
        return self._currentStage

    def getActiveStageLabel(self):
        return self._handle.product.getLabelForStage(self.getActiveStageName())

    def setActiveStageName(self, stageName):
        self.checkStageIsValid(stageName)
        self._currentStage = stageName

    def checkStageIsValid(self, stageName):
        stageNames = [ str(x.name) for x in self._handle.product.getStages() ]
        if stageName not in stageNames:
            raise errors.RbuildError('Unknown stage %r' % stageName)

    def getGroupFlavors(self):
        product = self._handle.product
        groupFlavors = [ (str(self.getBuildDefinitionGroupToBuild(x)),
                          str(x.getBuildBaseFlavor()))
                         for x in product.getBuildDefinitions() ]
        fullFlavors = self._handle.facade.conary._overrideFlavors(
                                             str(product.getBaseFlavor()),
                                             [x[1] for x in groupFlavors])
        fullFlavors = [ self._addInExtraFlavor(x) for x in fullFlavors ]
        return [(x[0][0], x[1]) for x in zip(groupFlavors, fullFlavors)]

    def getBuildDefinitionGroupToBuild(self, buildDefinition):
        """
        Find the source group to build for this build definition.
        @param buildDefinition: build definition defining the group to build.
        @type buildDefinition: L{proddef.Build}
        @rtype: string
        @return: Look for and return the first group that is found out of:
            - build definition source group
            - top level source group
            - build definition image group
            - top level image group
        """
        # getBuildSourceGroup takes care of looking at sourceGroup definied
        # on the build definition or at the top level.
        buildSourceGroup = buildDefinition.getBuildSourceGroup()

        if buildSourceGroup:
            return buildSourceGroup
        else:
            sourceGroupMatch = self.getSourceGroupMatch(buildDefinition)
            if sourceGroupMatch:
                return sourceGroupMatch

        # No sourceGroup defined anywhere that we can use, use an imageGroup.
        # getBuildImageGroup actually takes care of returning the top
        # level image group if there's not one set for the build
        # definition itself.
        return buildDefinition.getBuildImageGroup()

    def getSourceGroupMatch(self, buildDefinition):
        """
        Find a source group defined on a different build defintion that has a
        matching build flavor and image group as the given build definition.

        @param buildDefinition: build definition defining what flavor and
        image group to match.
        @type buildDefinition: L{proddef.Build}
        @rtype: string
        @return: source group name to build for this build definition. If none
        is found, return None.
        """
        # If there is no image group defined on buildDefinition, there's no
        # point in testing anything.
        if not buildDefinition.imageGroup:
            return None

        for bd in self._handle.product.getBuildDefinitions():
            # Test for flavor equality.
            if bd.getBuildBaseFlavor() == buildDefinition.getBuildBaseFlavor():

                # Test for image group equality.
                if bd.imageGroup and \
                   bd.imageGroup == buildDefinition.imageGroup:

                    # If defined, return the source group for this definition.
                    sourceGroup = bd.getBuildSourceGroup()
                    if sourceGroup:
                        return sourceGroup

        return None                    

    def getBuildsWithFullFlavors(self, stageName):
        """
        @param stageName: name of stage
        @type stageName: string
        @return: Tuples of (build, fullFlavor) for each build defined
        in stage C{stageName}
        @rtype: [(proddef.Build, string), ...]
        """
        product = self._handle.product
        builds = product.getBuildsForStage(stageName)
        flavors = [ x.getBuildBaseFlavor() for x in builds ]
        fullFlavors = self._handle.facade.conary._overrideFlavors(
                                             str(product.getBaseFlavor()),
                                             flavors)
        fullFlavors = [ self._addInExtraFlavor(x) for x in fullFlavors ]
        return zip(builds, fullFlavors)

    # temporary hack until RPCL-13 is complete
    def _addInExtraFlavor(self, flavor):
        majorArch = self._handle.facade.conary._getFlavorArch(flavor)
        if majorArch == 'x86':
            extraFlavor = ('~!grub.static'
                           ' is: x86(~i486,~i586,~i686,~cmov,~sse,~sse2)')
        else:
            extraFlavor = ('~grub.static is: x86_64'
                           ' x86(~i486,~i586,~i686,~cmov,~sse,~sse2)')
        return self._handle.facade.conary._overrideFlavors(flavor,
                                                           [extraFlavor])[0]


    def getPackageJobId(self):
        return self.getStatus('packageJobId')

    def getGroupJobId(self):
        return self.getStatus('groupJobId')

    def getImageJobId(self):
        return self.getStatus('imageJobId')

    def setPackageJobId(self, jobId):
        self.setStatus('packageJobId', jobId)

    def setGroupJobId(self, jobId):
        self.setStatus('groupJobId', jobId)

    def setImageJobId(self, jobId):
        self.setStatus('imageJobId', jobId)

    def getStatus(self, key):
        raise errors.IncompleteInterfaceError(
            'rBuild status storage unsupported for this configuration')

    def setStatus(self, key, value):
        raise errors.IncompleteInterfaceError(
            'rBuild status storage unsupported for this configuration')

    def getRbuildConfigData(self):
        raise errors.IncompleteInterfaceError(
            'rBuild configuration data unsupported for this configuration')

    def getRbuildConfigPath(self):
        # could save self.getRbuildConfigData() to a temporary file
        raise errors.RbuildError(
            'Not Yet Implemented')

    def getRmakeConfigData(self):
        raise errors.IncompleteInterfaceError(
            'rMake configuration data unsupported for this configuration')

    def getRmakeConfigPath(self):
        # could save self.getRmakeConfigData() to a temporary file
        raise errors.RbuildError(
            'Not Yet Implemented')

    def getPlatformAutoLoadRecipes(self):
        """
        Get the autoLoadRecipe configurations for the platform defined in the
        product definition.
        @return: autoLoadRecipe configurations
        @rtype: list of trove spec strings
        """
        autoLoadRecipes = []
        for alr in self._handle.product.getPlatformAutoLoadRecipes():
            autoLoadRecipes.append('%s=%s' % \
                (alr.getTroveName(), alr.getLabel()))
        return autoLoadRecipes

