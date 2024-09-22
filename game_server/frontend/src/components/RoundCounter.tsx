import { Progress } from "@mantine/core"
import { useConfigQuery } from "../scripts/query"
import { useInterval } from "@mantine/hooks"
import { useEffect, useState } from "react"
import { secondDurationToString } from "../scripts/time"


export const RoundCounter = () => {
    const config = useConfigQuery()
    
    const [roundInfo, setRoundInfo] = useState({
        startTime: new Date(0),
        roundLen: 0,
        currentRound: -1,
        currentRoundPercent: 0,
        hasStarted: false,
        timeForNextRound: 0,
        hasEnded: false
    })

    const updateRoundInfo = () => {
        if (config.data == null || config.isFetching) return
        const startGame = new Date(config.data.start_time)
        const endGame = config.data.end_time != null ? new Date(config.data.end_time) : null
        const now = new Date()
        const roundLen = config.data.round_len
        const nextRoundAt = new Date(startGame.getTime() + (config.data.current_round+2)*roundLen)
        const timeForNextRound = nextRoundAt.getTime() - now.getTime()
        const nextRoundPercent = Math.min(100, 100 - ((timeForNextRound / roundLen) * 100))
        setRoundInfo({
            startTime: new Date(config.data.start_time),
            roundLen: config.data.round_len,
            currentRound: config.data.current_round,
            currentRoundPercent: nextRoundPercent,
            hasStarted: startGame < now,
            timeForNextRound: (timeForNextRound <1000?0:timeForNextRound)/1000,
            hasEnded: endGame != null && endGame < now
        })
    }

    const timerScheduler = useInterval(updateRoundInfo, 1000, { autoInvoke: true })
    

    useEffect(() => {
        timerScheduler.start()
        return () => timerScheduler.stop()
    },[timerScheduler])


    useEffect(updateRoundInfo, [config.isFetching])

    return config.isSuccess?<>
        <small>{ !roundInfo.hasStarted ? "Game has not started yet" :roundInfo.hasEnded ? "Game has ended!" : roundInfo.currentRound==-1 ? "Game has started!" : `Round: ${config.data.current_round} - next round: ${secondDurationToString(roundInfo.timeForNextRound)}` }</small>
        <Progress size="lg" value={roundInfo.hasEnded ? 100 : config.data.current_round >= 0?roundInfo.currentRoundPercent:0} color="red"/>
    </>:<Progress size="lg" color="red" value={0}/>
}