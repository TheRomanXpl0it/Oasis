import { Box, Code, Space, Tooltip } from "@mantine/core";
import { TeamServiceScore } from "../scripts/query";
import { ImTarget } from "react-icons/im";
import { FaCircle, FaGlobe, FaPlug, FaPlus, FaWrench } from "react-icons/fa6";
import { FaSearch, FaShieldAlt } from "react-icons/fa";
import { IoSpeedometer } from "react-icons/io5";
import { modals } from "@mantine/modals";


export const ServiceScoreData = ({ score }: { score?: TeamServiceScore }) => {

    if (!score) return <></>

    const slaOk = score.sla_check == 101 && score.get_flag == 101 && score.put_flag == 101 ? true : false

    const showDetailModal = (title:string, msg:string) => {
        modals.open({
            title: title,
            children: (<Code block>{msg}</Code>),
            size: "lg",
            centered: true
        });
    }

    return <>
        <Box display="flex" style={{ alignItems: "center" }}>
            <FaGlobe size={16} /><Space w="xs" />{score.final_score.toFixed(2)}
        </Box>
        <Box display="flex" style={{ alignItems: "center" }}>
            <ImTarget size={16} /><Space w="xs" />{score.stolen_flags==0?"":"+"}{score.stolen_flags}
        </Box>
        <Box display="flex" style={{ alignItems: "center" }}>
            <FaShieldAlt size={16} /><Space w="xs" />{score.lost_flags==0?"":"-"}{score.lost_flags}
        </Box>
        <Box display="flex" style={{ alignItems: "center" }}>
            <IoSpeedometer size={16} /><Space w="xs" />{(score.sla*100).toFixed(2)}%<Space w="xs" />
            <FaCircle size={16} style={{ color: slaOk ? "green" : "red" }} />
        </Box>
        <Box display="flex" style={{ alignItems: "center" }}>
            <FaWrench size={16} /><Space w="xs" /><Box p={3} className="center-flex" style={{ borderRadius: "100px" }}>
                <Tooltip label={"SLA CHECK: "+score.sla_check_msg.substring(0,150)} position="top" withArrow color={score.sla_check == 101 ? "green": "red"}>
                    <Box
                        py={4} px={10}
                        style={{ backgroundColor: score.sla_check == 101 ? "green": "red", borderTopLeftRadius: 6, borderBottomLeftRadius: 6 }}
                        className="center-flex"
                        onClick={()=>showDetailModal(`SLA CHECK on ${score.service}`, score.sla_check_msg)}
                    >
                        <FaPlug size={14}/>
                    </Box>
                </Tooltip>
                <Tooltip label={"PUT FLAG: "+score.put_flag_msg.substring(0,150)} position="top" withArrow color={score.put_flag == 101 ? "green": "red"}>
                    <Box
                        py={4} px={10}
                        style={{ backgroundColor: score.put_flag == 101 ? "green": "red"}}
                        className="center-flex"
                        onClick={()=>showDetailModal(`PUT FLAG on ${score.service}`, score.put_flag_msg)}
                    >
                        <FaPlus size={14} />
                    </Box> 
                </Tooltip>
                <Tooltip label={"GET FLAG: "+score.get_flag_msg.substring(0,150)} position="top" withArrow color={score.get_flag == 101 ? "green": "red"}>
                    <Box
                        py={4} px={12}
                        style={{ backgroundColor: score.get_flag == 101 ? "green": "red", borderTopRightRadius: 6, borderBottomRightRadius: 6 }}
                        className="center-flex"
                        onClick={()=>showDetailModal(`GET FLAG on ${score.service}`, score.put_flag_msg)}
                    >
                        <FaSearch size={14} />
                    </Box>
                </Tooltip>
            </Box>
        </Box>
    </>
}