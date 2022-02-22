# Water Distribution Network Isolation Valve Analysis ToolKit

This repo contains code that can 
- Evaluate WDN network property change with respect to valve failure rates and network topology 
- Generate multi-scale isolation risk for pipes in the WDN 
- Find the optimal valve configuration for a WDN given the number of available valves to install 
- Rank valves to be maintained in priority based on network and hydraulic properties



## Data
The required data is the WDN's .inp file. 

## Running
### grid_network_simulation
This file contains a demonstration that generate arbitrary shaped WDNs and perform valve failure impact analysis on them. The supporting source code is contained in the scripts_topo file. 

The main purpose of this code is to understand the mechanism of how isolation valve failure impact WDN hydraulic performance. 

<p align="center">
<img src="https://github.com/rewu1993/valves/blob/master/imgs/network_generation_workflow.png" alt="high_level" class="design-primary" width="600px">
</p>


### riskmap_generation
This file demonstrates how to create a multi-scale pipe risk map for a WDN. The multi-scale pipe risk map provides a measure of failure risk for each pipe in the system regarding to different valve failure states. 

<p align="center">
<img src="https://github.com/rewu1993/wdn_valves/blob/master/imgs/pipe_riskmap_flowchart.png" alt="high_level" class="design-primary" width="600px">
</p>

### placement_optimization
This file demonstrates how to place isolation valves in a WDN to reach the minimal risk. 

<p align="center">
<img src="https://github.com/rewu1993/wdn_valves/blob/master/imgs/optimal_valve_flowchart.png" alt="high_level" class="design-primary" width="600px">
</p>



### valve_maintenance
This file demonstrates how to choose valves to maintain in priority using the network information (from the segment-valve graph) and hydraulic information (from the multi-scale pipe risk map) 

<p align="center">
<img src="https://github.com/rewu1993/wdn_valves/blob/master/imgs/valve_maintenance_flowchart.png" alt="high_level" class="design-primary" width="600px">
</p>

