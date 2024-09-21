import { Box, Code, Image, List, Space, Text, Title } from "@mantine/core"
import { Link } from "react-router-dom"
import { useConfigQuery } from "../scripts/query"
import { secondDurationToString } from "../scripts/time"


export const RulesContent = () => {

    const config = useConfigQuery()
    const nopTeam = config.data?.teams.find(team => team.nop)

    return config.isSuccess?<Box>
        <Title order={1} mt="lg">Rules</Title>
        <Text mt="lg">Welcome to OASIS, a simulation tool for Attack Defence CTF competitions.</Text>
        <List mt="lg">
            <List.Item>Open</List.Item>
            <List.Item>Attack & Defense</List.Item>
            <List.Item>Simple</List.Item>
            <List.Item>Infrastructure</List.Item>
            <List.Item>System</List.Item>
        </List>
        <Text mt="lg">The infrastruture is inspired from CyberChallenge A/D infrastructure, some parts of the rules are taken from there</Text>
        <Title order={2} mt="lg">Network and Setup</Title>
        <Text mt="lg">The game is played within the 10.0.0.0/8 subnet. Each team has its own vulnerable machine located at 10.60.team_id.1, while players connecting to the game network are assigned an ip in the 10.80.team_id.1/24 subnet.</Text>
        {nopTeam?<Text mt="md">The ip address <u>{nopTeam.host}</u> is assigned as NOP Team (Non-playing team) vulnerable VM, this VM will not be patched during the competition and its flags will not count towards the scoreboard you can use it to test your attacks.</Text>:null}
        <Text mt="md">All vulnerable VMs will be hosted by Oasis using <Link to="https://github.com/nestybox/sysbox">sysbox</Link>.</Text>
        <Box className="center-flex" mt="lg"><Image src="/images/network-1nop.svg" alt="Network Diagram" maw="800px"  /></Box>
        <Text mt="lg">The Game System is responsible for dispatching flags to the vulnerable machines, checking services integrity, hosting the scoreboard and updating scores. Participants are asked to attack vulnerable machines of other teams to retrieve proofs of successful exploitation (flags). Flags must be submitted to the flag submission service hosted by the organisers to score points. At the same time, teams must defend the vulnerable services installed on their VMs. Teams can do whatever they want within their network segment.</Text>
        <Text mt="md">Internet access is granted to install new software on the VM and on the laptops of participants, if needed. Organisers discourage interaction between CTF network and remote servers (e.g., starting attacks from cloud): bruteforce attacks or large computational resources are not required to succeed at the competition.</Text>
        <Text mt="md">Beware that if you mess up your vulnerable machine, all we can do is reset it to its original state (backup your exploits, tools and patches!). Resetting a vulnerable machine and return to a valid game state can take a long time and may lead to a high loss of points in the competition.</Text>
        <Text mt="md"><u>The only persistent data on the VM is /root/ folder, so is highly raccomanded to store your tools and exploits in that folder and to not reboot the VM</u></Text>
        <Text mt="md">Default SSH user for the VM is root and the password is your team token and will be sent to the teams before the competition start.</Text>
        <Title order={2} mt="lg">Scoring</Title>
        <Text mt="lg">The game is divided in rounds (also called ticks) with the duration of <u>{secondDurationToString(config.data.round_len/1000)}</u>. During each round, a bot will add new flags to your vulnerable machine. Moreover it will check the integrity of services by interacting with them and by retrieving the flags through legitimate accesses.</Text>
        <Text mt="md">Your team gains points by attacking other teams and by keeping services up and running. The total score is the sum of the individual scores for each service. The score per service is made of two components:</Text>
        <List mt="md">
            <List.Item>Offense: Points for flags captured from other teams and submitted to the Game System within their validity period</List.Item>
            <List.Item>SLA: % for the availability and correct behavior of your services (up tick / total tick)</List.Item>
        </List>
        <Text mt="md">The score for a flag of a service stolen by an attacking team attacker from a victim team victim will be assigned dynamically according to the formula:</Text>
        <Code block mt="md">
{`scale = 15 * sqrt(5) 
norm = ln(ln(5)) / 12 
offense_points[flag] = scale / (1+exp((sqrt(score[attacker][service]) - sqrt(score[victim][service]))*norm))
defense_points[flag] = min(victim_score, offense_points)`}
        </Code>
        <Text mt="md">According to the previous pseudocode, the attacking team will be assigned offense_points points and the victime team will loose defense_points points:</Text>
        <Code block mt="md">
{`# Service base points 
score[team][service] = 5000 
          
# Sum offensive points 
for flag in stolen_flags[team][service]:
  score[team][service] += offense_points[flag] 

# Substract defensive points 
for flag in lost_flags[team][service]: 
  score[team][service] -= defense_points[flag]`}
        </Code>
        <Text mt="md">The final team score will be the sum of the score for each service multiplied by its service SLA %.</Text>
        <Code block mt="md">
{`total_score[team] = 0 
            
for service in services: 
  # Compute SLA of the service
  sla[team][service] = ticks_up[team][service] / ticks[team][service] 
  # Limit scores to 0
  score[team][service] = max(0, score[team][service]) 
  # Add service score
  total_score[team] += score[team][service] * sla[team][service]`}
        </Code>
        <Text mt="md">Some consideration about the scoring system:</Text>
        <List mt="md">
            <List.Item>SLA % it is not added to the final score but it is a multiplying factor of the total score</List.Item>
            <List.Item>The score of a valid flag is correlated by the difference in service score of the two teams</List.Item>
            <List.Item>You will gain more points stealing flags from teams with higher service score</List.Item>
            <List.Item>You will gain less points stealing flags from teams with lower service score</List.Item>
        </List>
        <Text mt="md">For each team, the scoreboard will list the total score and for each service its flag points, the number of captured and lost flags, the SLA in % and three different status indicators for the various types of possible failures that can occured in your services.</Text>
        <Text mt="md">In each round, at most three different kind of checks will take place on your services:</Text>
        <List mt="md">
            <List.Item>Check SLA: it checks the availability of the service</List.Item>
            <List.Item>Put flag: it puts a new flag in the service</List.Item>
            <List.Item>Get flag: it try to retrieve a valid previously inserted flag. Please note that this check is not going to be performed if previous N put flag checks failed (where N is the flag lifetime).</List.Item>
        </List>
        <Text mt="md">Please note that, regarding the SLA %, a service is considered up (ticks_up[team][service]) only when every check performed in a round is successful (OK).</Text>
        <Text mt="md">Since there are countless ways to break a service, the scoreboard may be not provide full information if a service is marked as corrupt or mumble. Try to restore the service from your backup (please backup it before applying any patch) and check if the service is marked as up in few minutes.</Text>
        <Title order={2} mt="lg">Flags</Title>
        <Text mt="lg">A flag is a string made up of 31 uppercase alphabetic or numeric chars, followed by =. Each flag is matched by the regular expression <u>[A-Z0-9]{31}=</u>.</Text>
        <Text mt="md">You can submit stolen flags by performing an HTTP PUT request to the Game System at http://10.10.0.1:8080/flags. The flags must be submitted as an array of strings and the requests must contains the header X-Team-Token set to the team token given to the participants.</Text>
        <Text mt="md"><u>Note: the flag submission is rate limited to a maximum of 1 requests per {secondDurationToString(config.data.submitter_rate_limit/1000)} and each request will elaborate up to {config.data.submitter_flags_limit} flags, flags exceeding this limit will be ignored and must be submitted in another request.</u></Text>
        <Text mt="md">As an example, we provide a simple python snippet that accounts for the submission of two flag using.</Text>
        <Code block mt="md">
{`import requests

TEAM_TOKEN = '4242424242424242'
flags = ['AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=', 'BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=']

print(requests.put('http://10.10.0.1:8080/flags', headers={
    'X-Team-Token': TEAM_TOKEN
}, json=flags).text)`}
        </Code>
        <Text mt="md">The request will return a json array, for each sent flag you will receive an object in the form of:</Text>
        <Code block mt="md">
{`{
    'msg': f'[{flag}] {message}',
    'flag': flag,
    'status': true/false    
}`}
        </Code>
        <Text mt="md">Where message can be:</Text>
        <List mt="md">
            <List.Item>Accepted: X flag points</List.Item>
            <List.Item>Denied: invalid flag</List.Item>
            <List.Item>Denied: flag from nop team</List.Item>
            <List.Item>Denied: flag is your own</List.Item>
            <List.Item>Denied: flag too old</List.Item>
            <List.Item>Denied: flag already claimed</List.Item>
        </List>
        <Text mt="md">Please note that the request status code != 200 means that the request is malformed, team token header is not valid or the game is ended. In any case there is going to be a description of the problem in the response body.</Text>
        <Text mt="md">Flags are considered expired after {config.data.flag_expire_ticks} rounds. It means that teams have up to {secondDurationToString(config.data.round_len*config.data.flag_expire_ticks/1000)} to steal a flag and submit it. At the same time, the check bot will try to retrieve one of the last {config.data.flag_expire_ticks} flags from a service to check if the intended functionalities have been preserved and mark it as up.</Text>
        <Title order={2} mt="lg">Flag IDs</Title>
        <Text mt="lg">Some services have "Flag ID"s, additional information that you might need for an exploit. Usually this is the username of the Game System's account that stores the flag. The flag ids are only given for flags that are still valid.</Text>
        <Text mt="md">FlagIds can be retrieved by performing an HTTP GET request to the Game System at <Link to="http://10.10.0.1:8081/flagIds">http://10.10.0.1:8081/flagIds?team=10.60.0.1&service=ServiceName</Link>. The request query parameters are optional and can be used to filter the results.</Text>
        <Title order={2} mt="lg">Technical and Human Behaviour</Title>

        <Text mt="lg">We'd like everyone to enjoy a fair game. For this reason we ask you to follow these simple rules:</Text>
        <List mt="md">
            <List.Item>You are only allowed to attack targets on the subnet 10.60.0.0/16, Players are not allowed to attack each other (e.g. you can't break into opponents' laptops)</List.Item>
            <List.Item>No attacks against the infrastructure including denial-of-service (DoS), floods, DNS poisoning, ARP spoofing, MITM, etc...</List.Item>
            <List.Item>Unfair practices are not allowed. These include any action aimed at hindering others or exploiting advantages not related to skills and preparation. Attacks against the availability of other team services (breaking it, replacing/deleting flags, etc...) fall into this category.</List.Item>
            <List.Item>Sharing flags, exploits or hints between teams is severely prohibited and will grant you the exclusion from the competition</List.Item>
            <List.Item>When in doubt, ask to the organizers</List.Item>
        </List>
        <Space h="xl" />
    </Box>:<Box>Loading...</Box>
}