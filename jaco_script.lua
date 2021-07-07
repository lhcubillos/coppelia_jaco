function sysCall_init()
    corout=coroutine.create(coroutineMain)
end

function sysCall_actuation()
    if coroutine.status(corout)~='dead' then
        local ok,errorMsg=coroutine.resume(corout)
        if errorMsg then
            error(debug.traceback(corout,errorMsg),2)
        end
    end
end

function visualizePath(path)
    if not _lineContainer then
        _lineContainer=sim.addDrawingObject(sim.drawing_lines,3,0,-1,99999,{1,1,0})
    end
    sim.addDrawingObjectItem(_lineContainer,nil)
    if path then
        local lb=sim.setThreadAutomaticSwitch(false)
        local initConfig=getConfig()
        local l=#jh
        local pc=#path/l
        for i=1,pc-1,1 do
            local config1={path[(i-1)*l+1],path[(i-1)*l+2],path[(i-1)*l+3],path[(i-1)*l+4],path[(i-1)*l+5],path[(i-1)*l+6]}
            local config2={path[i*l+1],path[i*l+2],path[i*l+3],path[i*l+4],path[i*l+5],path[i*l+6]}
            setConfig(config1)
            local lineDat=sim.getObjectPosition(simTip,-1)
            setConfig(config2)
            local p=sim.getObjectPosition(simTip,-1)
            lineDat[4]=p[1]
            lineDat[5]=p[2]
            lineDat[6]=p[3]
            sim.addDrawingObjectItem(_lineContainer,lineDat)
        end
        setConfig(initConfig)
        sim.setThreadAutomaticSwitch(lb)
    end
    sim.switchThread()
end

function _getJointPosDifference(startValue,goalValue,isRevolute)
    local dx=goalValue-startValue
    if (isRevolute) then
        if (dx>=0) then
            dx=math.mod(dx+math.pi,2*math.pi)-math.pi
        else
            dx=math.mod(dx-math.pi,2*math.pi)+math.pi
        end
    end
    return(dx)
end

function _applyJoints(jointHandles,joints)
    for i=1,#jointHandles,1 do
        sim.setJointTargetPosition(jointHandles[i],joints[i])
    end
end

function generatePathLengths(path)
    -- Returns a table that contains a distance along the path for each path point
    local d=0
    local l=#jh
    local pc=#path/l
    local retLengths={0}
    for i=1,pc-1,1 do
        local config1={path[(i-1)*l+1],path[(i-1)*l+2],path[(i-1)*l+3],path[(i-1)*l+4],path[(i-1)*l+5],path[(i-1)*l+6],path[(i-1)*l+7]}
        local config2={path[i*l+1],path[i*l+2],path[i*l+3],path[i*l+4],path[i*l+5],path[i*l+6],path[i*l+7]}
        d=d+getConfigConfigDistance(config1,config2)
        retLengths[i+1]=d
    end
    return retLengths
end

function getShiftedMatrix(matrix,localShift,dir)
    -- Returns a pose or matrix shifted by vector localShift
    local m={}
    for i=1,12,1 do
        m[i]=matrix[i]
    end
    m[4]=m[4]+dir*(m[1]*localShift[1]+m[2]*localShift[2]+m[3]*localShift[3])
    m[8]=m[8]+dir*(m[5]*localShift[1]+m[6]*localShift[2]+m[7]*localShift[3])
    m[12]=m[12]+dir*(m[9]*localShift[1]+m[10]*localShift[2]+m[11]*localShift[3])
    return m
end

function validationCb(config,auxData)
    local retVal=true
    local prev={}
    for i=1,#jh,1 do
        prev[i]=sim.getJointPosition(jh[i])
        sim.setJointPosition(jh[i],config[i])
    end
    for i=1,#collisionPairs/2,1 do
        if sim.checkCollision(collisionPairs[(i-1)*2+1],collisionPairs[(i-1)*2+2])>0 then
            retVal=false
            break
        end
    end
    for i=1,#jh,1 do
        sim.setJointPosition(jh[i],prev[i])
    end
    return retVal
end

function findCollisionFreeConfig(matrix)
    -- Here we search for a robot configuration..
    -- 1. ..that matches the desired pose (matrix)
    -- 2. ..that does not collide in that configuration
    sim.setObjectMatrix(simTarget,-1,matrix)

    -- This robot has 4 joints that have a huge range (i.e. -10'000 - +10'000 degrees)
    -- And since we do not want to search that huge space, we limit the range around the current configuration
    -- We actually do the same during path search
    local cc=getConfig()
    local jointLimitsL={}
    local jointRanges={}
    for i=1,#jh,1 do
        jointLimitsL[i]=cc[i]-360*math.pi/180
        if jointLimitsL[i]<-10000 then jointLimitsL[i]=-10000 end
        jointRanges[i]=720*math.pi/180
        if cc[i]+jointRanges[i]>10000 then jointRanges[i]=10000-cc[i] end
    end
    jointLimitsL[2]=47*math.pi/180
    jointRanges[2]=266*math.pi/180
    jointLimitsL[3]=19*math.pi/180
    jointRanges[3]=322*math.pi/180
    simIK.applySceneToIkEnvironment(ikEnv,ikGroup)
    local c=simIK.getConfigForTipPose(ikEnv,ikGroup,ikJoints,0.65,2,{1,1,1,0.25},validationCb,nil,nil,jointLimitsL,jointRanges)
    return c
end

function findSeveralCollisionFreeConfigs(matrix,trialCnt,maxConfigs)
    -- Here we search for several robot configurations...
    -- 1. ..that matches the desired pose (matrix)
    -- 2. ..that does not collide in that configuration
    -- 3. ..that does not collide and that can perform the IK linear approach
    sim.setObjectMatrix(simTarget,-1,matrix)
    local cc=getConfig()
    local cs={}
    local l={}
    for i=1,trialCnt,1 do
        local c=findCollisionFreeConfig(matrix)
        if c then
            local dist=getConfigConfigDistance(cc,c)
            local p=0
            local same=false
            for j=1,#l,1 do
                if math.abs(l[j]-dist)<0.001 then
                    -- we might have the exact same config. Avoid that
                    same=true
                    for k=1,#jh,1 do
                        if math.abs(cs[j][k]-c[k])>0.01 then
                            same=false
                            break
                        end
                    end
                end
                if same then
                    break
                end
            end
            if not same then
                cs[#cs+1]=c
                l[#l+1]=dist
            end
        end
        if #l>=maxConfigs then
            break
        end
    end
    if #cs==0 then
        cs=nil
    end
    return cs
end

function getConfig()
    -- Returns the current robot configuration
    local config={}
    for i=1,#jh,1 do
        config[i]=sim.getJointPosition(jh[i])
    end
    return config
end

function setConfig(config)
    -- Applies the specified configuration to the robot
    if config then
        for i=1,#jh,1 do
            sim.setJointPosition(jh[i],config[i])
        end
    end
end

function getConfigConfigDistance(config1,config2)
    -- Returns the distance (in configuration space) between two configurations
    local d=0
    for i=1,#jh,1 do
        local dx=(config1[i]-config2[i])*metric[i]
        d=d+dx*dx
    end
    return math.sqrt(d)
end

function getPathLength(path)
    -- Returns the length of the path in configuration space
    local d=0
    local l=#jh
    local pc=#path/l
    for i=1,pc-1,1 do
        local config1={path[(i-1)*l+1],path[(i-1)*l+2],path[(i-1)*l+3],path[(i-1)*l+4],path[(i-1)*l+5],path[(i-1)*l+6]}
        local config2={path[i*l+1],path[i*l+2],path[i*l+3],path[i*l+4],path[i*l+5],path[i*l+6]}
        d=d+getConfigConfigDistance(config1,config2)
    end
    return d
end

function _findPath(startConfig,goalConfigs)
    
    -- Following because the robot has "strange" joint limits, e.g. +-10'000, and searching such a large
    -- space would be inefficient for path planning
    local jointLimitsL={}
    local jointLimitsH={}
    for i=1,#jh,1 do
        jointLimitsL[i]=startConfig[i]-360*math.pi/180
        if jointLimitsL[i]<-10000 then jointLimitsL[i]=-10000 end
        jointLimitsH[i]=startConfig[i]+360*math.pi/180
        if jointLimitsH[i]>10000 then jointLimitsH[i]=10000 end
    end
    jointLimitsL[2]=47*math.pi/180
    jointLimitsH[2]=313*math.pi/180
    jointLimitsL[3]=19*math.pi/180
    jointLimitsH[3]=341*math.pi/180

    local task=simOMPL.createTask('task')
    simOMPL.setAlgorithm(task,OMPLAlgo)
    local jSpaces={}
    for i=1,#jh,1 do
        local proj=i
        if i>3 then proj=0 end
        jSpaces[#jSpaces+1]=simOMPL.createStateSpace('j_space'..i,simOMPL.StateSpaceType.joint_position,jh[i],{jointLimitsL[i]},{jointLimitsH[i]},proj)
    end
    simOMPL.setStateSpace(task,jSpaces)
    simOMPL.setCollisionPairs(task,collisionPairs)
    simOMPL.setStartState(task,startConfig)
    simOMPL.setGoalState(task,goalConfigs[1])
    for i=2,#goalConfigs,1 do
        simOMPL.addGoalState(task,goalConfigs[i])
    end
    simOMPL.setup(task)
    local l=nil
    local res,path=simOMPL.compute(task,maxOMPLCalculationTime,-1,200)
    if path then
        visualizePath(path)
        l=getPathLength(path)
    end
    simOMPL.destroyTask(task)
    return path,l
end

function findPath(startConfig,goalConfigs)
    -- This function will search for a path between the specified start configuration,
    -- and several of the specified goal configurations.
    local onePath,onePathLength=_findPath(startConfig,goalConfigs)
    return onePath,generatePathLengths(onePath)
end

function generateIkPath(startConfig,goalPose,steps,ignoreCollisions)
    -- Generates (if possible) a linear, collision free path between a robot config and a target pose
    local lb=sim.setThreadAutomaticSwitch(false)
    local currentConfig=getConfig()
    setConfig(startConfig)
    sim.setObjectMatrix(simTarget,-1,goalPose)
    local val=validationCb
    if ignoreCollisions then
        val=nil
    end
    simIK.applySceneToIkEnvironment(ikEnv,ikGroup)
    local c=simIK.generatePath(ikEnv,ikGroup,ikJoints,ikTip,steps,val)
    setConfig(currentConfig)
    sim.setThreadAutomaticSwitch(lb)
    if #c/6>0 then
        local d={}
        for i=1,#c/6,1 do
            for j=1,6,1 do
                d[(i-1)*6+j]=c[(i-1)*6+j]
            end
        end
        return d, generatePathLengths(d)
    end
end

function executeMotion(path,lengths,maxVel,maxAccel,maxJerk)
    dt=sim.getSimulationTimeStep()

    -- 1. Make sure we are not going too fast for each individual joint (i.e. calculate a correction factor (velCorrection)):
    jointsUpperVelocityLimits={}
    for j=1,6,1 do
        jointsUpperVelocityLimits[j]=sim.getObjectFloatParam(jh[j],sim.jointfloatparam_upper_limit)
    end
    velCorrection=1

    sim.setThreadSwitchTiming(200)
    while true do
        posVelAccel={0,0,0}
        targetPosVel={lengths[#lengths],0}
        pos=0
        res=0
        previousQ={path[1],path[2],path[3],path[4],path[5],path[6]}
        local rMax=0
        rmlHandle=sim.rmlPos(1,0.0001,-1,posVelAccel,{maxVel*velCorrection,maxAccel,maxJerk},{1},targetPosVel)
        while res==0 do
            res,posVelAccel,sync=sim.rmlStep(rmlHandle,dt)
            if (res>=0) then
                l=posVelAccel[1]
                for i=1,#lengths-1,1 do
                    l1=lengths[i]
                    l2=lengths[i+1]
                    if (l>=l1)and(l<=l2) then
                        t=(l-l1)/(l2-l1)
                        for j=1,6,1 do
                            q=path[6*(i-1)+j]+_getJointPosDifference(path[6*(i-1)+j],path[6*i+j],jt[j]==sim.joint_revolute_subtype)*t
                            dq=_getJointPosDifference(previousQ[j],q,jt[j]==sim.joint_revolute_subtype)
                            previousQ[j]=q
                            r=math.abs(dq/dt)/jointsUpperVelocityLimits[j]
                            if (r>rMax) then
                                rMax=r
                            end
                        end
                        break
                    end
                end
            end
        end
        sim.rmlRemove(rmlHandle)
        if rMax>1.001 then
            velCorrection=velCorrection/rMax
        else
            break
        end
    end
    sim.setThreadSwitchTiming(2)

    -- 2. Execute the movement:
    posVelAccel={0,0,0}
    targetPosVel={lengths[#lengths],0}
    pos=0
    res=0
    jointPos={}
    rmlHandle=sim.rmlPos(1,0.0001,-1,posVelAccel,{maxVel*velCorrection,maxAccel,maxJerk},{1},targetPosVel)
    while res==0 do
        dt=sim.getSimulationTimeStep()
        res,posVelAccel,sync=sim.rmlStep(rmlHandle,dt)
        if (res>=0) then
            l=posVelAccel[1]
            for i=1,#lengths-1,1 do
                l1=lengths[i]
                l2=lengths[i+1]
                if (l>=l1)and(l<=l2) then
                    t=(l-l1)/(l2-l1)
                    for j=1,6,1 do
                        jointPos[j]=path[6*(i-1)+j]+_getJointPosDifference(path[6*(i-1)+j],path[6*i+j],jt[j]==sim.joint_revolute_subtype)*t
                    end
                    _applyJoints(jh,jointPos)
                    break
                end
            end
        end
        sim.switchThread()
    end
    sim.rmlRemove(rmlHandle)
end

function coroutineMain()
    -- START HERE:
    jh={-1,-1,-1,-1,-1,-1}
    jt={-1,-1,-1,-1,-1,-1}
    for i=1,6,1 do
        jh[i]=sim.getObjectHandle('Jaco_joint'..i)
        jt[i]=sim.getJointType(jh[i])
    end
    simBase=sim.getObjectHandle(sim.handle_self)    
    simTarget=sim.getObjectHandle('Jaco_target')
    simTip=sim.getObjectHandle('Jaco_tip')

    -- Prepare the ik group, using the convenience function 'simIK.addIkElementFromScene':
    ikEnv=simIK.createEnvironment()
    ikGroup=simIK.createIkGroup(ikEnv)
    local ikElement,simToIkMap=simIK.addIkElementFromScene(ikEnv,ikGroup,simBase,simTip,simTarget,simIK.constraint_pose)
    ikJoints={}
    for i=1,#jh,1 do
        ikJoints[i]=simToIkMap[jh[i]]
    end
    ikTip=simToIkMap[simTip]

    target0=sim.getObjectHandle('jacoTarget0')
    target1=sim.getObjectHandle('jacoTarget1')
    target2=sim.getObjectHandle('jacoTarget2')
    target3=sim.getObjectHandle('jacoTarget3')
    local collection=sim.createCollection(0)
    sim.addItemToCollection(collection,sim.handle_tree,simBase,0)
    -- 2 collision pairs: the first for robot self-collision detection, the second for robot-environment collision detection:
    collisionPairs={collection,collection,collection,sim.handle_all}
    maxVel=1    
    maxAccel=1
    maxJerk=8000
    forbidLevel=0
    metric={0.2,1,0.8,0.1,0.1,0.1}
    ikSteps=20
    maxOMPLCalculationTime=4 -- for one calculation. Higher is better, but takes more time
    OMPLAlgo=simOMPL.Algorithm.PRMstar -- the OMPL algorithm to use

    local initConfig=getConfig()

    -- Move close to the first cup (with motion planning):
    local m=getShiftedMatrix(sim.getObjectMatrix(target1,-1),{-0.05,0,0.1},-1)
    local configs=findSeveralCollisionFreeConfigs(m,300,5)
    path,lengths=findPath(getConfig(),configs)
    if path then
        visualizePath(path)
        executeMotion(path,lengths,maxVel,maxAccel,maxJerk)
    end

    -- Move very close to the first cup (with IK):
    local m=getShiftedMatrix(sim.getObjectMatrix(target1,-1),{0,0.01,0},-1)
    path,lengths=generateIkPath(getConfig(),m,ikSteps,true)
    if path then
        executeMotion(path,lengths,maxVel,maxAccel,maxJerk)
    end


    -- close the hand
    sim.setIntegerSignal("hand",1)
    sim.wait(1.25)

    -- Lift the cup and move closer to the second cup (with IK):
    local m=sim.getObjectMatrix(target2,-1)
    path,lengths=generateIkPath(getConfig(),m,ikSteps,true)
    if path then
        executeMotion(path,lengths,maxVel,maxAccel,maxJerk)
    end

    -- Ask Mico to start its movement sequence:
    sim.setIntegerSignal('yourTurnMico',1)

    -- Pour the cup content into the other cup  (with IK):
    local m=sim.getObjectMatrix(target3,-1)
    path,lengths=generateIkPath(getConfig(),m,ikSteps,true)
    if path then
        executeMotion(path,lengths,maxVel,maxAccel,maxJerk)
    end

    -- Move back to configuration before pouring (with IK):
    local m=sim.getObjectMatrix(target2,-1)
    path,lengths=generateIkPath(getConfig(),m,ikSteps,true)
    if path then
        executeMotion(path,lengths,maxVel,maxAccel,maxJerk)
    end

    -- Put the cup back onto the table (with IK):
    local m=getShiftedMatrix(sim.getObjectMatrix(target1,-1),{0,0.01,0},-1)
    path,lengths=generateIkPath(getConfig(),m,ikSteps,true)
    if path then
        executeMotion(path,lengths,maxVel,maxAccel,maxJerk)
    end



    -- open the hand:
    sim.setIntegerSignal("hand",0)
    sim.wait(1.0)


    -- Move a bit back (with IK):
    local m=getShiftedMatrix(sim.getObjectMatrix(target1,-1),{-0.05,0,0.1},-1)
    path,lengths=generateIkPath(getConfig(),m,ikSteps,true)
    if path then
        executeMotion(path,lengths,maxVel,maxAccel,maxJerk)
    end


    -- move back to the initial configuration:
    path,lengths=findPath(getConfig(),{initConfig})
    if path then
        visualizePath(path)
        executeMotion(path,lengths,maxVel,maxAccel,maxJerk)
    end
end
