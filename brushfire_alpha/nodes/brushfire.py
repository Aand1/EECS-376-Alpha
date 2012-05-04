class BrushFire():
    def __init__(self, c1, c2, numCells, size=10, goal=None):
        self.globalc1 = c1
        self.globalc2 = c2
        self.numCells = numCells

        self.globalMap = self.createGrid(numCells)

        self.localMap = None
        self.localx = None
        self.localy = None
        self.size = size
        
        self.goal = goal
        self.robotPos = None

    def createGrid(self,numCells=50):
        '''
        This method uses the specified corners and the numCells to create a 2d array that will store the values used in the brushfire algorithm
        '''
        # empty list
        globalMap = list()
        
        for i in range(numCells):
            globalMap.append(list())
            for j in range(numCells):
                globalMap[i].append(0) # 0 is blank

        return globalMap
        
    def updateGlobalGrid(self, obstacles):
        '''
        This method is responsible for taking in new obstacles
        and adding them to the global obstacle list
        '''
        globalMap = self.globalMap
        numCells = self.numCells

        for point in obstacles:
            try:
                # see if the point has a corresponding point in the grid
                gridPoint = self.transformMapToGrid(point)
                globalMap[gridPoint[0]][gridPoint[1]] = -1
            except IndexError:
                # if the point isn't in the grid then ignore it
                pass

        self.globalMap = globalMap

    def extractLocal(self, x, y):
        '''
        This method takes in an x and y location for the robot
        It then takes a subsection of the global that is 
        size wide and size high.
        
        This local map will be used by the brushfire algorithm.
        '''

        # Get the robot's current position in the global grid
        self.robot = self.transformMapToGrid((x,y), self.globalc1, self.globalc2, self.numCells)

        self.localx = (self.robot[0]-size,self.robot[0]+size)
        self.localy = (self.robot[1]-size,self.robot[1]+size)
        
        # will store the local map
        localMap = list()

        for i in range(self.localx[0],self.localx[1]):
            localMap.append(list())
            for j in range(self.localy[0],self.localy[1]):
                if(i >= 0 and i < self.numCells and j >= 0 and j < self.numCells):
                    localMap[-1].append(self.globalMap[i][j])
                else:
                    localMap[-1].append(1)

        self.localMap

    def transformGridToMap(self, point):
        c1 = self.globalc1
        c2 = self.globalc2
        numCells = self.numCells
        if(point[0] < 0 or point[0] >= numCells):
            raise IndexError
        if(point[1] < 0 or point[1] >= numCells):
            raise IndexError

        # width and height of grid cells
        xStep = abs(c1[0] - c2[0])/float(numCells)
        yStep = abs(c1[1] - c2[1])/float(numCells)

        x = xStep*point[0] + min(c1[0],c2[0])
        y = yStep*point[1] + min(c1[1],c2[1])

        return (x,y)

    def transformMapToGrid(self, point):
        c1 = self.globalc1
        c2 = self.globalc2
        numCells = self.numCells
        # width and height of grid cells
        xStep = float(abs(c1[0] - c2[0]))/numCells
        yStep = float(abs(c1[1] - c2[1]))/numCells

        # translate the goal point to grid space
        xIndex = int((point[0]-min(c1[0],c2[0]))/xStep)
        yIndex = int((point[1]-min(c1[1],c2[1]))/yStep)

        # make sure the indices of the point are within
        # the specified grid dimensions
        if(xIndex >= numCells or xIndex < 0):
            raise IndexError
        if(yIndex >= numCells or yIndex < 0):
            raise IndexError
        
        return (xIndex,yIndex)

    def transformLocalToGlobal(self, point):
        '''
        Transform a point in the localMap to the corresponding
        point in the globalMap
        '''
        return (point[0]+self.localx[0],point[1]+self.localy[0])

    def getNeighbors(self, point):
        '''
        given a point in grid space find all of viable neighbors
        return this as a list of tuples
        '''
        neighbors = list()

        # up
        x = point[0]
        y = point[1] + 1
        if(y < self.height and y >=0 and x < self.height and x >= 0):
            neighbors.append((x,y))

        # up right
        x = point[0] + 1
        y = point[1] + 1
        if(y < self.height and y >=0 and x < self.height and x >= 0):
            neighbors.append((x,y))

        # right
        x = point[0] + 1
        y = point[1]
        if(y < self.height and y >=0 and x < self.height and x >= 0):
            neighbors.append((x,y))

        # down right
        x = point[0] + 1
        y = point[1] - 1
        if(y < self.height and y >=0 and x <self.height and x >= 0):
            neighbors.append((x,y))

        # down
        x = point[0]
        y = point[1] - 1
        if(y < self.height and y >=0 and x < self.height and x >= 0):
            neighbors.append((x,y))

        # down left
        x = point[0] - 1
        y = point[1] - 1
        if(y < self.height and y >=0 and x < self.height and x >= 0):
            neighbors.append((x,y))

        # left
        x = point[0] - 1
        y = point[1]
        if(y < self.height and y >=0 and x < self.height and x >= 0):
            neighbors.append((x,y))

        # up left
        x = point[0] - 1
        y = point[1] + 1
        if(y < self.height and y >=0 and x < self.height and x >= 0):
            neighbors.append((x,y))

        return neighbors

    def brushfire(self):
        '''
        Given a square grid of obstacles runs brushfire and returns grid
        '''
        self.height = len(localMap)
        seenZero = True
        # if there are no zeros seen in a loop, we are done with brushfire
        while seenZero:
            seenZero = False
            for r,row in enumerate(localMap):
                for c,col in enumerate(localMap[r]):
                    if localMap[r][c] == 0:
                        seenZero = True
                        neighbors = self.getNeighbors((r,c))
                        for point in neighbors:
                            localMap[point[0]][point[1]]+=1
        return localMap

    def computePath(self):
        '''
        take grid of points passed through brushfire and returns list of points
        to follow
        '''
        pass

    def updateGoal(self, goal):
        '''
        Will save the given goal point to the class
        '''
        self.goal = goal

    def __str__(self):
        '''
        Displays the current local map as ASCII art
        '''
        numSpaces = 3

        if(self.localMap is None):
            return 'None'

        display = '-'*numSpaces
        display += '|'

        # print the column headings
        for i in range(self.size):
            display += printSpacedCharacter(i,numSpaces)

        display = display + '\n'

        # add a horizontal rule
        for i in range(self.size):
            display += '-'*numSpaces

        display = display + '\n'

        # print the weights
        for i,row in enumerate(self.localMap):
            for j,cell in enumerate(row):
                # print row heading
                if(j == 0):
                    display += printSpacedCharacter(i,numSpaces) + '|'
                display += printSpacedCharacter(cell,numSpaces)
            display += '\n'

        return display
    
    def printSpacedCharacter(char, numSpaces):
        '''
        Takes in a number of spaces and chars and outputs
        the character with the correct spacing
        '''
        spacedString = str(char)

        spacedString += (numSpaces - len(spacedString))*' '
        
        return spacedString
            
        