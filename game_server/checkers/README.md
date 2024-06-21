# CybersecNatLab - AD Demo

## Services checkers

|  #  | service | store | checker                                  |
| :-: | :------ | :---: | ---------------------------------------- |
|  0  | Notes   |   1   | [checker](/checkers/service1/checker.py) |
|  1  | Polls   |   1   | [checker](/checkers/service2/checker.py) |

## How to run

- Check sla: `ACTION=CHECK_SLA TEAM_ID=0 ROUND=0 ./checker.py`
- Put flag: `ACTION=PUT_FLAG TEAM_ID=0 ROUND=0 FLAG=FLAG ./checker.py`
- Get flag: `ACTION=GET_FLAG TEAM_ID=0 ROUND=0 FLAG=FLAG ./checker.py`
