import { useQuery } from "@tanstack/react-query";


const baseUrl = import.meta.env.DEV?"http://127.0.0.1:8888":""


type Config = {
    teams: {id: number, name: string, host: string, image: string, nop: boolean}[],
    services: string[],
    start_time: string,
    round_len: number,
    flag_expire_ticks: number,
    submitter_flags_limit: number,
    submitter_rate_limit: number
    current_round: number
}

export type TeamServiceScore = {
    service: string,
    stolen_flags: number,
    lost_flags: number,
    sla: number,
    score: number,
    ticks_up: number,
    ticks_down: number,
    put_flag: number,
    put_flag_msg: string,
    get_flag: number,
    get_flag_msg: string,
    sla_check: number,
    sla_check_msg: string,
    final_score: number
}

type TeamScores = {
    team: string,
    score: number,
    services: TeamServiceScore[]
}

type Scoreboard = {
    round: number,
    scores: TeamScores[]
}

type TeamScoreboardDetails = {
    round: number,
    score: TeamScores
}[]

type ChartInfo = {
    rounds: number,
    scores: {
        team: string,
        score: number,
    }[]
}[]



export const useConfigQuery = () => useQuery({
    queryKey: ["config"],
    queryFn: async () => await fetch(baseUrl+"/api/config").then(c => c.json()) as Config,
    refetchInterval: 1000*3,
    refetchIntervalInBackground: true,
    staleTime: 1000*3,
})

export const useScoreboardQuery = () => useQuery({
    queryKey: ["scoreboard"],
    queryFn: async () => await fetch(baseUrl+"/api/scoreboard").then(c => c.json()) as Scoreboard
})

export const useTeamQuery = (teamId: string) => useQuery({
    queryKey: ["scoreboard", "team", teamId],
    queryFn: async () => await fetch(baseUrl+`/api/team/${teamId}`).then(c => c.json()) as TeamScoreboardDetails
})

export const useChartQuery = () => useQuery({
    queryKey: ["scoreboard", "chart"],
    queryFn: async () => await fetch(baseUrl+"/api/chart").then(c => c.json()) as ChartInfo
})

export const useTeamSolver = () => {
    const configData = useConfigQuery()
    return (host:string) => {
        return configData.data?.teams.find(t => t.host == host)
    }
}