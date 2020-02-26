import sys
import math

WIDTH = 16000
HEIGHT = 9000
RANGE = 2200

EXPANSION = 1
HUNT = 2
EXPLORATION = 3
CAMPING = 4
HELPING = 5
INTERCEPT = 6
COMING_BACK = 7


def distance(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


class Buster:

    def __init__(self, ID, x, y, state, value):
        self.ID = ID
        self.stunAvailability = 0
        self.activity = EXPANSION
        self.radarAvailibility = True
        self.ejectAvailability = True
        self.update(x, y, state, value)

    def update(self, x, y, state, value):
        self.x = x
        self.y = y
        self.state = state
        self.value = value


class myBuster(Buster):

    def updateActivity(self, activity):
        self.previousActivity = activity
        self.activity = activity

    def setDestination(self, x, y):
        self.destinationX = x
        self.destinationY = y
        print(str(x) + ' ' + str(y) + ' ' + str(self.activity), file=sys.stderr)

    def destinationReached(self):
        if distance(self.x, self.y, self.destinationX, self.destinationY) < 5:
            return True
        else:
            return False

    def destinationNearlyReached(self):
        if distance(self.x, self.y, self.destinationX, self.destinationY) < 1000:
            return True
        else:
            return False

    def canComeBack(self):
        if self.state == 1:
            self.activity = COMING_BACK
            return True
        return False

    def moveToDestination(self):
        print("MOVE " + str(self.destinationX) + " " + str(self.destinationY))

    def move(self, x, y):
        print("MOVE " + str(x) + " " + str(y))

    def bust(self, ghostId):
        print("BUST " + str(ghostId))

    def release(self):
        self.activity = self.previousActivity
        print("RELEASE")

    def stun(self, enemyId):
        print("STUN " + str(enemyId))

    def useRadar(self):
        self.radarAvailibility = False
        print("RADAR")

    def eject(self, x, y):
        if self.ejectAvailability and self.state == 1:
            print("EJECT " + str(x) + " " + str(y))
            self.ejectAvailability = False
            return True
        return False


class enemyBuster(Buster):
    def __init__(self, ID, x, y, state, value):
        self.ID = ID
        self.update(x, y, state, value)


class Ghost:

    def __init__(self, ID, x, y, stamina, numOfBusters):
        self.ID = ID
        self.x = x
        self.y = y
        self.stamina = stamina
        self.numOfBusters = numOfBusters

    def updateLastSeen(self, turn):
        self.lastSeen = turn


class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.lastVisited = -100
        self.targeted = False


class Grid:
    def __init__(self):
        self.nodes = []
        for y in range(1500, 7500 + 1, 3000):
            for x in range(1500, 14500 + 1, 3250):
                node = Node(x, y)
                self.nodes.append(node)


class multiAgent:

    def __init__(self, teamId, numBusters):
        self.freeGhosts = []
        self.trappedGhosts = []
        self.enemyGhosts = []
        self.currentlyVisibleGhosts = []
        self.myBusters = []
        self.enemyBusters = []
        self.numBusters = numBusters
        self.teamId = teamId
        self.turn = 0
        self.ghostToHelpWith = -1
        self.enemiesToBeStunned = []
        self.grid = Grid()
        self.setBaseCoordinates()

    def setBaseCoordinates(self):
        if self.teamId == 0:
            self.baseX = 0
            self.baseY = 0
            self.enemyBaseX = WIDTH
            self.enemyBaseY = HEIGHT
        else:
            self.baseX = WIDTH
            self.baseY = HEIGHT
            self.enemyBaseX = 0
            self.enemyBaseY = 0

    def updateVisitedNodes(self):
        for i in range(self.numBusters):
            for j in range(len(self.grid.nodes)):
                if distance(self.myBusters[i].x, self.myBusters[i].y, self.grid.nodes[j].x,
                            self.grid.nodes[j].y) <= 100:
                    self.grid.nodes[j].lastVisited = self.turn
                    self.grid.nodes[j].targeted = False

    def explore(self, busterIndex):
        cost = -1000 * (self.turn - self.grid.nodes[0].lastVisited) - distance(self.myBusters[busterIndex].x,
                                                                               self.myBusters[busterIndex].y,
                                                                               self.grid.nodes[0].x,
                                                                               self.grid.nodes[0].y)
        cost += min(distance(0, HEIGHT, self.grid.nodes[0].x, self.grid.nodes[0].y),
                    distance(WIDTH, 0, self.grid.nodes[0].x, self.grid.nodes[0].y))
        minCost = cost
        minInd = 0
        for i in range(1, len(self.grid.nodes)):
            if not self.grid.nodes[i].targeted:
                cost = -1000 * (self.turn - self.grid.nodes[i].lastVisited) - distance(self.myBusters[busterIndex].x,
                                                                                       self.myBusters[busterIndex].y,
                                                                                       self.grid.nodes[i].x,
                                                                                       self.grid.nodes[i].y)
                cost += min(distance(0, HEIGHT, self.grid.nodes[i].x, self.grid.nodes[i].y),
                            distance(WIDTH, 0, self.grid.nodes[i].x, self.grid.nodes[i].y))
                if cost < minCost:
                    minCost = cost
                    minInd = i
        self.grid.nodes[minInd].targeted = True
        return self.grid.nodes[minInd].x, self.grid.nodes[minInd].y

    def checkCorners(self, busterIndex):
        corners = [[0, HEIGHT], [WIDTH, 0]]
        return corners[busterIndex % 2][0], corners[busterIndex % 2][1]

    def updateMyBusters(self, ID, x, y, state, value):
        n = 0
        for i in range(len(self.myBusters)):
            if self.myBusters[i].ID == ID:
                self.myBusters[i].x = x
                self.myBusters[i].y = y
                self.myBusters[i].state = state
                self.myBusters[i].value = value
                n = 1
        if n == 0:
            buster = myBuster(ID, x, y, state, value)
            self.myBusters.append(buster)

    def updateEnemyBusters(self, enemyBusters):
        self.enemyBusters = enemyBusters[:]

    def initalizeExpansion(self):
        length = (HEIGHT - 2 * RANGE) * math.sqrt(2)
        toAdd = RANGE * math.sqrt(2)
        for i in range(self.numBusters):
            self.myBusters[i].updateActivity(EXPANSION)
            x = int(math.sin((i + 1) * math.pi / 2 / (self.numBusters + 1)) * 6400)
            y = int(math.cos((i + 1) * math.pi / 2 / (self.numBusters + 1)) * 6400)
            if self.teamId == 1:
                x = WIDTH - x
                y = HEIGHT - y
            self.myBusters[i].setDestination(x, y)

    def setVisibleGhosts(self, ghosts):
        self.currentlyVisibleGhosts = []
        for ghost in ghosts:
            self.currentlyVisibleGhosts.append(ghost)

    def updateGhostInfo(self, ID, x, y, stamina, value, type):
        if type == 0:
            n = 0
            for i in range(len(self.trappedGhosts)):
                if self.trappedGhosts[i].ID == ID:
                    self.trappedGhosts[i].x = x
                    self.trappedGhosts[i].y = y
                    self.trappedGhosts[i].stamina = 0
                    n = 1
            if n == 0:
                ghost = Ghost(ID, x, y, stamina, value)
                self.trappedGhosts.append(ghost)
            for i in range(len(self.freeGhosts)):
                if self.freeGhosts[i].ID == ID:
                    self.freeGhosts = self.freeGhosts[:i] + self.freeGhosts[i + 1:]
                    break
        elif type == 1:
            n = 0
            for i in range(len(self.freeGhosts)):
                if self.freeGhosts[i].ID == ID:
                    self.freeGhosts[i].x = x
                    self.freeGhosts[i].y = y
                    self.freeGhosts[i].stamina = stamina
                    n = 1
            if n == 0:
                ghost = Ghost(ID, x, y, stamina, value)
                self.freeGhosts.append(ghost)
        elif type == 2:
            n = 0
            for i in range(len(self.enemyGhosts)):
                if self.enemyGhosts[i].ID == ID:
                    self.enemyGhosts[i].x = x
                    self.enemyGhosts[i].y = y
                    self.enemyGhosts[i].stamina = 0
                    n = 1
            if n == 0:
                ghost = Ghost(ID, x, y, stamina, value)
                self.enemyGhosts.append(ghost)
            for i in range(len(self.freeGhosts)):
                if self.freeGhosts[i].ID == ID:
                    self.freeGhosts = self.freeGhosts[:i] + self.freeGhosts[i + 1:]
                    break

    def closestGhost(self, buster):
        flag = False
        if len(self.freeGhosts) > 0:
            min = 99999999999999
            for ghost in self.freeGhosts:
                if self.turn > 30:
                    cost = int(distance(ghost.x, ghost.y, buster.x, buster.y) / 800) + ghost.stamina + int(
                        distance(ghost.x, ghost.y, self.baseX, self.baseY) / 800)
                else:
                    cost = int(distance(ghost.x, ghost.y, self.enemyBaseX, self.enemyBaseY) / 800)
                if cost < min and (self.turn >= 50 or (self.turn < 50 and ghost.stamina < 40)):
                    min = cost
                    minId = ghost.ID
                    flag = True
            if flag:
                return minId
        return -1

    def closestVisibleGhost(self, buster):
        flag = False
        if len(self.currentlyVisibleGhosts) > 0:
            min = 99999999999999
            for ghost in self.currentlyVisibleGhosts:
                if self.turn > 30:
                    cost = int(distance(ghost.x, ghost.y, buster.x, buster.y) / 800) + int(
                        ghost.stamina / (ghost.numOfBusters + 1)) + int(
                        distance(ghost.x, ghost.y, self.baseX, self.baseY) / 800)
                else:
                    cost = int(distance(ghost.x, ghost.y, self.enemyBaseX, self.enemyBaseY) / 800) + ghost.stamina
                if cost < min and (self.turn >= 50 or (self.turn < 50 and ghost.stamina < 40)):
                    min = cost
                    minId = ghost.ID
                    flag = True
            if flag:
                return minId
        return -1

    def findGhost(self, ID):
        if ID == -1:
            return self.baseX, self.baseY
        for ghost in self.freeGhosts:
            if ghost.ID == ID:
                return ghost.x, ghost.y

    def findVisibleGhost(self, ID):
        if ID == -1:
            return self.baseX, self.baseY
        for ghost in self.currentlyVisibleGhosts:
            if ghost.ID == ID:
                return ghost.x, ghost.y

    def returnGhostById(self, ID):
        for ghost in self.currentlyVisibleGhosts:
            if ghost.ID == ID:
                return ghost
        return -1

    def findMyBuster(self, ID):
        for buster in self.myBusters:
            if buster.ID == ID:
                return buster.x, buster.y

    def returnMyBusterById(self, ID):
        for buster in self.myBusters:
            if buster.ID == ID:
                return buster

    def tryBust(self, busterIndex):
        tooClose = False
        for i in range(len(self.currentlyVisibleGhosts)):
            dist = distance(self.myBusters[busterIndex].x, self.myBusters[busterIndex].y,
                            self.currentlyVisibleGhosts[i].x, self.currentlyVisibleGhosts[i].y)
            if dist >= 900 and dist <= 1760 and (
                    self.turn >= 50 or (self.turn < 50 and self.currentlyVisibleGhosts[i].stamina < 40)):
                if self.turn >= 6:
                    if (distance(self.currentlyVisibleGhosts[i].x, self.currentlyVisibleGhosts[i].y, self.baseX,
                                 self.baseY) > distance(self.myBusters[busterIndex].x, self.myBusters[busterIndex].y,
                                                        self.baseX, self.baseY) and self.turn <= 30) or self.turn > 30:
                        self.myBusters[busterIndex].bust(self.currentlyVisibleGhosts[i].ID)
                        return True
            elif dist < 900 and (self.turn >= 50 or (
                    self.turn < 50 and self.currentlyVisibleGhosts[i].stamina < 40)) and self.turn >= 6:
                ghostX = self.currentlyVisibleGhosts[i].x
                ghostX = self.currentlyVisibleGhosts[i].y
                tooClose = True
        if tooClose:
            self.myBusters[busterIndex].move(self.baseX, self.baseY)
            return True

        return False

    def deleteGhost(self, ID):
        for i in range(len(self.freeGhosts)):
            if self.freeGhosts[i].ID == ID:
                self.freeGhosts = self.freeGhosts[:i] + self.freeGhosts[i + 1:]
                return 0

    def tryEject(self, busterIndex):
        for enemy in self.enemyBusters:
            if distance(enemy.x, enemy.y, self.baseX, self.baseY) <= distance(self.baseX, self.baseY,
                                                                              self.myBusters[busterIndex].x,
                                                                              self.myBusters[busterIndex].y):
                return False
        for buster in self.myBusters:
            if distance(self.baseX, self.baseY, self.myBusters[busterIndex].x, self.myBusters[busterIndex].y) <= 5000:
                if distance(buster.x, buster.y, self.baseX, self.baseY) < distance(self.baseX, self.baseY,
                                                                                   self.myBusters[busterIndex].x,
                                                                                   self.myBusters[busterIndex].y):
                    # return False
                    return self.myBusters[busterIndex].eject(self.baseX, self.baseY)
        return False

    def tryRelease(self, busterIndex):
        if distance(self.myBusters[busterIndex].x, self.myBusters[busterIndex].y, self.baseX, self.baseY) <= 1600:
            self.myBusters[busterIndex].release()
            return True
        return False

    def willAnyoneStun(self, enemyBusterId, myBusterId):
        index = -1
        for i in range(len(self.enemyBusters)):
            if self.enemyBusters[i].ID == enemyBusterId:
                index = i
                break
        if index != -1:
            for buster in self.myBusters:
                if buster.ID != myBusterId:
                    if buster.state == 0 and buster.stunAvailability == 0 and distance(buster.x, buster.y,
                                                                                       self.enemyBusters[index].x,
                                                                                       self.enemyBusters[
                                                                                           index].y) <= 1760:
                        return True
        return False

    def somewhereIsSaucyGhost(self):
        if self.busterInDanger() != -1:
            return True
        for ghost in self.freeGhosts:
            if ghost.stamina < 10:
                return True
        for buster in self.enemyBusters:
            if buster.state == 1:
                return True
        return False

    def busterInDanger(self):
        for buster in self.myBusters:
            if buster.state == 1 or buster.state == 3 or buster.state == 2:
                ghost = (self.returnGhostById(buster.value))
                if ghost != -1:
                    if self.howManyMyBustersBusting(buster.value) < ghost.numOfBusters:
                        return buster.ID
                for enemy in self.enemyBusters:
                    if distance(buster.x, buster.y, enemy.x, enemy.y) <= RANGE and buster.state != 2:
                        return buster.ID
                    elif distance(buster.x, buster.y, enemy.x, enemy.y) <= RANGE and buster.state == 2:
                        for ghost in self.currentlyVisibleGhosts:
                            if distance(buster.x, buster.y, ghost.x, ghost.y) <= RANGE:
                                print("XDDXDXDXDXDDXDDXDXD", file=sys.stderr)
                                return buster.ID
        return -1

    def howManyMyBustersBusting(self, ghostId):
        n = 0
        for buster in self.myBusters:
            if buster.state == 3 and buster.value == ghostId:
                n += 1
        return n

    def tryStun(self, busterIndex):
        flag = False
        if self.myBusters[busterIndex].stunAvailability == 0:
            for i in range(len(self.enemyBusters)):
                if self.somewhereIsSaucyGhost():
                    if (self.myBusters[busterIndex].state == 0 or ((self.myBusters[busterIndex].state == 1 or
                                                                    self.myBusters[
                                                                        busterIndex].state == 3) and not self.willAnyoneStun(
                            self.enemyBusters[i].ID, self.myBusters[busterIndex].ID))) and self.enemyBusters[
                        i].ID not in self.enemiesToBeStunned:
                        if distance(self.myBusters[busterIndex].x, self.myBusters[busterIndex].y,
                                    self.enemyBusters[i].x, self.enemyBusters[i].y) <= 1760:
                            if self.enemyBusters[i].state == 1:
                                self.myBusters[busterIndex].stun(self.enemyBusters[i].ID)
                                self.myBusters[busterIndex].stunAvailability = 20
                                self.enemiesToBeStunned.append(self.enemyBusters[i].ID)
                                return True
                            elif self.myBusters[busterIndex].state == 3 and self.returnGhostById(
                                    self.myBusters[i].value) != -1 and self.enemyBusters[i].state == 0:
                                if self.returnGhostById(self.myBusters[i].value).stamina / self.returnGhostById(
                                        self.myBusters[i].value).numOfBusters < 10:
                                    self.myBusters[busterIndex].stun(self.enemyBusters[i].ID)
                                    self.myBusters[busterIndex].stunAvailability = 20
                                    self.enemiesToBeStunned.append(self.enemyBusters[i].ID)
                                    return True
                            elif self.enemyBusters[i].state == 3 and self.returnGhostById(
                                    self.enemyBusters[i].value) != -1:
                                if self.returnGhostById(self.enemyBusters[i].value).stamina / self.returnGhostById(
                                        self.enemyBusters[i].value).numOfBusters <= 2:
                                    self.myBusters[busterIndex].stun(self.enemyBusters[i].ID)
                                    self.myBusters[busterIndex].stunAvailability = 20
                                    self.enemiesToBeStunned.append(self.enemyBusters[i].ID)
                                    return True
                            elif self.enemyBusters[i].state == 2 and self.enemyBusters[i].value == 1:
                                busterToStun = self.enemyBusters[i].ID
                                flag = True
                            elif self.enemyBusters[i].state == 0:
                                busterToStun = self.enemyBusters[i].ID
                                flag = True
        if flag:
            self.myBusters[busterIndex].stun(busterToStun)
            self.myBusters[busterIndex].stunAvailability = 20
            self.enemiesToBeStunned.append(busterToStun)
        return flag

    def tryStunCamping(self, busterIndex):
        if self.myBusters[busterIndex].state == 0 and self.myBusters[busterIndex].stunAvailability == 0:
            for i in range(len(self.enemyBusters)):
                if distance(self.myBusters[busterIndex].x, self.myBusters[busterIndex].y, self.enemyBusters[i].x,
                            self.enemyBusters[i].y) <= 1760:
                    if self.enemyBusters[i].state == 1:
                        self.myBusters[busterIndex].stun(self.enemyBusters[i].ID)
                        self.myBusters[busterIndex].stunAvailability = 20
                        return True
        return False

    def setInterceptionMode(self, busterIndex):
        for enemy in self.enemyBusters:
            if enemy.state == 1 and self.enemyBaseX - enemy.x != 0:
                a = (self.enemyBaseY - enemy.y) / (self.enemyBaseX - enemy.x)
                b = enemy.y - a * enemy.x
                finalX = math.sqrt(RANGE * RANGE / (a * a + 1))
                finalY = a * finalX + b
                if self.teamId == 0:
                    finalX = WIDTH - finalX
                    finalY = a * finalX + b
                if self.myBusters[busterIndex].state == 2:
                    stunTimer = self.myBusters[busterIndex].value
                else:
                    stunTimer = 0
                if self.myBusters[busterIndex].stunAvailability <= int(
                        distance(finalX, finalY, self.myBusters[busterIndex].x, self.myBusters[busterIndex].y) / 800):
                    if int(distance(finalX, finalY, enemy.x, enemy.y) / 800) >= int(
                            distance(finalX, finalY, self.myBusters[busterIndex].x,
                                     self.myBusters[busterIndex].y) / 800) + stunTimer:
                        self.myBusters[busterIndex].activity = INTERCEPT
                        self.myBusters[busterIndex].setDestination(int(finalX), int(finalY))
                    elif self.myBusters[busterIndex].activity == INTERCEPT:
                        self.myBusters[busterIndex].activity = self.myBusters[busterIndex].previousActivity
                elif self.myBusters[busterIndex].activity == INTERCEPT:
                    self.myBusters[busterIndex].activity = self.myBusters[busterIndex].previousActivity

    def setCampingMode(self, busterIndex):
        if self.numBusters == 2:
            limitA = 250
            limitB = 250
        else:
            limitA = 150
            limitB = 200
        if self.turn >= limitA and self.turn <= limitB and self.myBusters[busterIndex].activity != INTERCEPT:
            self.myBusters[busterIndex].updateActivity(CAMPING)
        elif self.turn > limitB and self.myBusters[busterIndex].activity != INTERCEPT:
            self.myBusters[busterIndex].updateActivity(EXPLORATION)

    def setHelpingMode(self, busterIndex):
        ID = self.busterInDanger()
        if ID != -1 and ID != self.myBusters[busterIndex].ID:
            self.myBusters[busterIndex].activity = HELPING
            busterInDanger = self.returnMyBusterById(ID)
            contestedGhost = self.returnGhostById(busterInDanger.value)
            if contestedGhost != -1:
                if contestedGhost.numOfBusters > 0:
                    if distance(self.myBusters[busterIndex].x, self.myBusters[busterIndex].y, busterInDanger.x,
                                busterInDanger.y) < int(
                            contestedGhost.stamina / contestedGhost.numOfBusters) or self.howManyMyBustersBusting(
                            busterInDanger.value) == contestedGhost.numOfBusters / 2:
                        return busterInDanger.x, busterInDanger.y
            if contestedGhost == -1:
                return busterInDanger.x, busterInDanger.y
        if self.myBusters[busterIndex].activity != INTERCEPT:
            self.myBusters[busterIndex].activity = self.myBusters[busterIndex].previousActivity
        return -1, -1

    def setCampingCoordinates(self, busterIndex):
        length = 6000 / math.sqrt(2)
        x = length * (busterIndex + 1) / (self.numBusters + 1)
        y = length - x
        if self.teamId == 0:
            x = WIDTH - x
            y = HEIGHT - y
        x = int(x)
        y = int(y)
        return x, y

    def updateStunAvailability(self):
        for i in range(len(self.myBusters)):
            if self.myBusters[i].stunAvailability > 0:
                self.myBusters[i].stunAvailability -= 1

    def isGhostVisible(self, ID):
        for ghost in self.currentlyVisibleGhosts:
            if ghost.ID == ID:
                return True
        return False

    def eliminateFreeGhosts(self):
        indexes = []
        for i in range(len(self.freeGhosts)):
            if not self.isGhostVisible(self.freeGhosts[i].ID):
                for buster in self.myBusters:
                    if distance(buster.x, buster.y, self.freeGhosts[i].x, self.freeGhosts[i].y) <= 500:
                        print(self.freeGhosts[i].ID, file=sys.stderr)
                        indexes.append(i)
                        break
        print("INDEXES", indexes, file=sys.stderr)
        for index in reversed(indexes):
            self.freeGhosts = self.freeGhosts[:index] + self.freeGhosts[index + 1:]

    def debugging(self):
        print("MY BUSTERS", file=sys.stderr)
        print("ID, X, Y, DESTINATION_X, DESTINATION_Y, STATE, VALUE, STUN, ACTIVITY", file=sys.stderr)
        for i in range(len(self.myBusters)):
            print(str(i + 1) + ")", self.myBusters[i].ID, self.myBusters[i].x, self.myBusters[i].y,
                  self.myBusters[i].destinationX, self.myBusters[i].destinationY, self.myBusters[i].state,
                  self.myBusters[i].value, self.myBusters[i].stunAvailability, self.myBusters[i].activity,
                  self.myBusters[i].previousActivity, file=sys.stderr)
        print("\nENEMY BUSTERS", file=sys.stderr)
        for i in range(len(self.enemyBusters)):
            print(str(i + 1) + ")", self.enemyBusters[i].ID, self.enemyBusters[i].x, self.enemyBusters[i].y,
                  self.enemyBusters[i].state, self.enemyBusters[i].value, file=sys.stderr)
        print("\nVISIBLE GHOSTS", file=sys.stderr)
        for i in range(len(self.currentlyVisibleGhosts)):
            print(str(i + 1) + ")", self.currentlyVisibleGhosts[i].ID, self.currentlyVisibleGhosts[i].x,
                  self.currentlyVisibleGhosts[i].y, self.currentlyVisibleGhosts[i].stamina,
                  self.currentlyVisibleGhosts[i].numOfBusters, file=sys.stderr)
        print("\nFREE GHOSTS", file=sys.stderr)
        for i in range(len(self.freeGhosts)):
            print(str(i + 1) + ")", self.freeGhosts[i].ID, self.freeGhosts[i].x, self.freeGhosts[i].y,
                  self.freeGhosts[i].stamina, self.freeGhosts[i].numOfBusters, file=sys.stderr)
        print("\nENEMY GHOSTS", file=sys.stderr)
        for i in range(len(self.enemyGhosts)):
            print(str(i + 1) + ")", self.enemyGhosts[i].ID, self.enemyGhosts[i].x, self.enemyGhosts[i].y,
                  self.enemyGhosts[i].stamina, file=sys.stderr)
        '''
        print("\n\nNODES", file=sys.stderr)
        for i in range(len(self.grid.nodes)):
            print(self.grid.nodes[i].x, self.grid.nodes[i].y, self.grid.nodes[i].lastVisited, file=sys.stderr)
            if (i + 1) % 16 == 0:
                print("\n", file=sys.stderr)
         '''

    def bustersWorkflow(self):
        self.updateStunAvailability()
        # self.eliminateFreeGhosts()
        self.enemiesToBeStunned = []

        for i in range(self.numBusters):
            if not self.myBusters[i].canComeBack():
                self.setCampingMode(i)
                self.setInterceptionMode(i)
                helpX, helpY = self.setHelpingMode(i)

        self.debugging()
        self.eliminateFreeGhosts()

        for i in range(self.numBusters):
            if not self.myBusters[i].canComeBack():
                self.setCampingMode(i)
                self.setInterceptionMode(i)
                helpX, helpY = self.setHelpingMode(i)

            if self.myBusters[i].activity == EXPANSION:
                if not self.tryBust(i):
                    if self.myBusters[i].destinationReached():
                        if not self.myBusters[i].radarAvailibility:
                            ghostId = self.closestGhost(self.myBusters[i])
                            if ghostId != -1:
                                ghostX, ghostY = self.findGhost(ghostId)
                                self.myBusters[i].setDestination(ghostX, ghostY)
                                self.myBusters[i].updateActivity(HUNT)
                                self.myBusters[i].moveToDestination()
                            else:
                                x, y = self.explore(i)
                                self.myBusters[i].setDestination(x, y)
                                self.myBusters[i].updateActivity(EXPLORATION)
                                self.myBusters[i].moveToDestination()
                        else:
                            self.myBusters[i].useRadar()
                    else:
                        self.myBusters[i].moveToDestination()

            elif self.myBusters[i].activity == HUNT:
                if not self.tryStun(i):
                    if not self.tryBust(i):
                        ghostId = self.closestVisibleGhost(self.myBusters[i])
                        if ghostId != -1:
                            ghostX, ghostY = self.findVisibleGhost(ghostId)
                            self.myBusters[i].setDestination(ghostX, ghostY)
                        else:
                            ghostId = self.closestGhost(self.myBusters[i])
                            if ghostId != -1:
                                ghostX, ghostY = self.findGhost(ghostId)
                                self.myBusters[i].setDestination(ghostX, ghostY)
                            else:
                                x, y = self.explore(i)
                                self.myBusters[i].updateActivity(EXPLORATION)
                        self.myBusters[i].moveToDestination()

            elif self.myBusters[i].activity == EXPLORATION:
                if not self.tryStun(i):
                    if not self.tryBust(i):
                        ghostId = self.closestVisibleGhost(self.myBusters[i])
                        if ghostId != -1:
                            x, y = self.findGhost(ghostId)
                            self.myBusters[i].setDestination(x, y)
                            self.myBusters[i].updateActivity(HUNT)
                        elif self.myBusters[i].destinationReached():
                            x, y = self.explore(i)
                            self.myBusters[i].setDestination(x, y)
                        self.myBusters[i].moveToDestination()

            elif self.myBusters[i].activity == CAMPING:
                if not self.tryStunCamping(i):
                    if not self.tryBust(i):
                        ghostId = self.closestVisibleGhost(self.myBusters[i])
                        if ghostId != -1:
                            ghostX, ghostY = self.findGhost(ghostId)
                            self.myBusters[i].setDestination(ghostX, ghostY)
                        else:
                            x, y = self.setCampingCoordinates(i)
                            self.myBusters[i].setDestination(x, y)
                        self.myBusters[i].moveToDestination()

            elif self.myBusters[i].activity == HELPING:
                x = self.myBusters[i].x
                y = self.myBusters[i].y
                if distance(x, y, helpX, helpY) > 3000:
                    self.myBusters[i].move(helpX, helpY)
                else:
                    if not self.tryStun(i):
                        if not self.tryBust(i):
                            self.myBusters[i].move(helpX, helpY)

            elif self.myBusters[i].activity == INTERCEPT:
                flag = 0
                if self.myBusters[i].destinationNearlyReached():
                    flag = 1
                    if not self.tryStun(i):
                        if not self.tryBust(i):
                            flag = 2
                if flag == 1:
                    ghostId = self.closestVisibleGhost(self.myBusters[i])
                    if ghostId != -1:
                        ghostX, ghostY = self.findVisibleGhost(ghostId)
                        self.myBusters[i].setDestination(ghostX, ghostY)
                        self.myBusters[i].updateActivity(HUNT)
                    else:
                        ghostId = self.closestGhost(self.myBusters[i])
                        if ghostId != -1:
                            ghostX, ghostY = self.findGhost(ghostId)
                            self.myBusters[i].setDestination(ghostX, ghostY)
                            self.myBusters[i].updateActivity(HUNT)
                        else:
                            x, y = self.explore(i)
                            self.myBusters[i].updateActivity(EXPLORATION)
                if flag == 0 or flag == 2:
                    self.myBusters[i].moveToDestination()

            elif self.myBusters[i].activity == COMING_BACK:
                if not self.tryStun(i):
                    if not self.tryRelease(i):
                        if self.myBusters[i].state == 2:
                            self.myBusters[i].activity = self.myBusters[i].previousActivity
                            self.myBusters[i].moveToDestination()
                        else:
                            self.myBusters[i].move(self.baseX, self.baseY)
                else:
                    self.myBusters[i].activity = self.myBusters[i].previousActivity

        self.updateVisitedNodes()


# Send your busters out into the fog to trap ghosts and bring them home!

busters_per_player = int(input())  # the amount of busters you control
ghost_count = int(input())  # the amount of ghosts on the map
my_team_id = int(input())  # if this is 0, your base is on the top left of the map, if it is one, on the bottom right

GHOST = -1
gameAI = multiAgent(my_team_id, busters_per_player)

# game loop
while True:
    entities = int(input())  # the number of busters and ghosts visible to you
    myBusters = []
    ghosts = []
    enemyBusters = []
    for i in range(entities):
        # entity_id: buster id or ghost id
        # y: position of this buster / ghost
        # entity_type: the team id if it is a buster, -1 if it is a ghost.
        # state: For busters: 0=idle, 1=carrying a ghost. For ghosts: remaining stamina points.
        # value: For busters: Ghost id being carried/busted or number of turns left when stunned. For ghosts: number of busters attempting to trap this ghost.
        entity_id, x, y, entity_type, state, value = [int(j) for j in input().split()]
        if entity_type == my_team_id:
            gameAI.updateMyBusters(entity_id, x, y, state, value)
            if state == 1:
                gameAI.updateGhostInfo(value, x, y, 0, value, 0)
        elif entity_type == GHOST:
            gameAI.updateGhostInfo(entity_id, x, y, state, value, 1)
            ghost = Ghost(entity_id, x, y, state, value)
            ghosts.append(ghost)
        else:
            buster = enemyBuster(entity_id, x, y, state, value)
            enemyBusters.append(buster)
            if state == 1:
                gameAI.updateGhostInfo(value, x, y, 0, value, 2)
    gameAI.updateEnemyBusters(enemyBusters)
    gameAI.setVisibleGhosts(ghosts)
    if gameAI.turn == 0:
        gameAI.initalizeExpansion()

    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr)

    # MOVE x y | BUST id | RELEASE | STUN id | RADAR | EJECT x y
    gameAI.bustersWorkflow()

    gameAI.turn += 1