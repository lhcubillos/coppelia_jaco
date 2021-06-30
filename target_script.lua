function sysCall_init()
    objectToFollowPath=sim.getObjectHandle(sim.handle_self)
    orientation = {-0.7071068287, 0, 0, 0.7071068287}
    velocity= nil
    posAlongPath = 0
    previousSimulationTime = 0
    initial_point = nil
    distance = 5.0
    vel_norm1 = nil
    corout = coroutine.create(coroutineMain)
end

function sysCall_actuation()
    if coroutine.status(corout)~='dead' then
        local ok,errorMsg=coroutine.resume(corout)
        if errorMsg then
            error(debug.traceback(corout,errorMsg),2)
        end
    end
end

function coroutineMain()
    sim.setThreadAutomaticSwitch(false)
    -- create path to point given by xyz
    
    while true do
        local t=sim.getSimulationTime()
        
        if initial_point ~= nil and vel_norm1 ~= nil then
            -- Check if it works without checking against length.
            posAlongPath = posAlongPath + velocity * (t - previousSimulationTime)
            local pos = (initial_point + posAlongPath * vel_norm1):t():totable()[1]
            -- Go to position and orientation
            sim.setObjectPosition(objectToFollowPath,-1,pos)
            sim.setObjectQuaternion(objectToFollowPath,-1,orientation)
        end
        previousSimulationTime = t
        -- Switch to main thread
        sim.switchThread()
    end
end

function createPath()
    -- vel_x = sim.getFloatSignal("vel_x")
    posAlongPath = 0
    vel_x = 0.0
    vel_y = sim.getFloatSignal("vel_y")
    vel_z = sim.getFloatSignal("vel_z")
    if vel_x == 0.0 and vel_y == 0.0 and vel_z == 0.0 then
        return
    end
    -- Set posAlongPath to 0
    local curr_pos = Vector3(sim.getObjectPosition(objectToFollowPath, -1))
    -- Set x position zero
    curr_pos[1] = 0.0
    local vel = Vector3({vel_x,vel_y,vel_z})
    velocity = vel:norm()
    vel_norm1 = vel / velocity
    initial_point = curr_pos:copy()
end
