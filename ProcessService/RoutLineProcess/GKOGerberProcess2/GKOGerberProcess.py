from ProcessService.RoutLineProcess.GKOGerberProcess2.ProcessBase import ProcessBase


class GKOGerberProcess(ProcessBase):
    def __init__(self, gerberLayer):
        ProcessBase.__init__(self, gerberLayer)

    def PreProc(self):
        sets = self.sets
        self.OverLapping_Set(sets)
        sets = self.Regenerate(sets)
        self.CutSet_Set(sets)
        sets = self.Regenerate(sets)
        self.CutLine_Set(sets)
        sets = self.Regenerate(sets)
        self.OverLapping_Set(sets)
        sets = self.Regenerate(sets)
        self.CutSet_Set(sets)
        sets = self.Regenerate(sets)
        self.CutLine_Set(sets)
        sets = self.Regenerate(sets)
        self.CombineSets(sets)
        self.sets = sets
        pass

    def LastProc(self):
        sets = self.sets
        for set in sets:
            set.endPoint_isolated = False
            set.HasCompared = False
        self.CombineSets(sets)
        for set in sets:
            set.endPoint_isolated = False
            set.HasCompared = False
        box = self.gerberLayer.bounding_box
        offset = 0.005
        box = ((box[0][0] + offset, box[0][1] - offset), (box[1][0] + offset, box[1][1] - offset))
        newsets = []
        for set in sets:
            if not self.box1_in_box2(set.bounding_box, box) or True:
                newsets.append(set)
        self.CombineSets(newsets)
        self.sets = newsets

    def box1_in_box2(self, box1, box2):
        return box1[0][0] > box2[0][0] and box1[0][1] < box2[0][1] and box1[1][0] > box2[1][0] and box1[1][1] < box2[1][1]
