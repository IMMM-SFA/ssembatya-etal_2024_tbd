# -*- coding: utf-8 -*-
"""
Spyder Editor
This is a temporary script file.
"""

import pandas as pd
import math
import numpy as np
import os
from shutil import copy
from pathlib import Path
########################################
# LOAD ALLOCATION FROM BALANCING AUTHORITY to NODES

########################################


rcp= [ "rcp45cooler_ssp3_"  , "rcp45hotter_ssp3_",  "rcp85cooler_ssp3_" ,  "rcp85hotter_ssp3_"]


#year
year=np.arange(2020, 2100, 1,dtype=int)

#model type
model= ["base" , "stdd", "high", "ultra"]

#simple or coal
UC = '_simple'

#scaling
trans_p = 0
#trans_p = [25,50,75,100]

#node number
node_number=150

config="150simple0_"
df_full = pd.read_csv('ERCOT_Bus.csv',header=0)
z = pd.read_csv('ERCOT_Bus.csv',header=0)
Zones = list(z['ZoneName'].unique())
for rr in rcp:
    
    for MM in model:
        
        for yy in year:
            
            #loading the load for every year
            df_load = pd.read_csv( "resultsml_hecc/" + str(rr) + "results" + "/" + str(rr) + MM + "_load_tot.csv",header=0)
            #limit rows to 8760
            df_load=df_load.iloc[:8760,:]
            #2099 has 5 missing values at the end. Filling them with the last known value
            if yy == 2099 or yy == 2049:
                df_load=df_load.interpolate()
            path=str(Path.cwd()) + str(Path('/Exp' + str(rr) + MM + '_'+ str(config) + str(yy)))
            os.makedirs(path,exist_ok=True)
            
            #T_p = trans_p/100
            T_p_new = trans_p
            
            FN = 'Results_' + str(node_number) + '.xlsx'
            
         
            # selected nodes
            df_selected = pd.read_excel(FN,sheet_name = 'Bus', header=0)
            buses = list(df_selected['bus_i'])
            
            # pull selected nodes out of 
            selected_zones = []
            for b in buses:
                Zone = df_full.loc[df_full['Number']==b,'ZoneName']
                Zone = Zone.reset_index(drop=True)
                selected_zones.append(Zone[0])
            
            df_selected['Zone'] = selected_zones
            
            zones = []
            for i in buses:
                z = df_full.loc[df_full['Number']==i,'ZoneName'].values[0]
                if z in zones:
                    pass
                else:
                    zones.append(z)
                
            # calculate nodal weights within each Zone
            
            Zone_totals = []
            for b in Zones:
                sample = list(df_selected.loc[df_selected['Zone']==b,'Pd'])
                corrected = [0 if x<0 else x for x in sample]
                Zone_totals.append(sum(corrected))
            
            Z = sum(Zone_totals)
            # Zone_totals = np.column_stack((Zones,Zone_totals))
            # df_Zone_totals = pd.DataFrame(Zone_totals)
            # df_Zone_totals.columns = ['Name','Total']
            
            weights = []
            for i in range(0,len(df_selected)):
                area = df_selected.loc[i,'Zone']
                if df_selected.loc[i,'Pd'] <0:
                    weights.append(0)
                else:        
                    W = (df_selected.loc[i,'Pd']/Z)
                    weights.append(W)
            df_selected['Load Weight'] = weights
            
            idx = 0
            w= 0
            T = np.zeros((8760,len(buses)))
            
            for i in range(0,len(df_selected)):
                    
                #load for original node
                name = df_selected.loc[i,'Zone']
                
                abbr = str(yy)
                weight = df_selected.loc[i,'Load Weight']
                T[:,i] = T[:,i] + np.reshape(df_load[abbr].values*weight,(8760,))
            
            for i in range(0,len(buses)):
                buses[i] = 'bus_' + str(buses[i])
            
            df_C = pd.DataFrame(T)
            df_C.columns = buses
            df_C.to_csv('nodal_load.csv',index=None)   
            
            copy('nodal_load.csv',path)
            
            #############
            # GENERATORS
            
            df_wind = pd.read_csv('BA_wind.csv',header=0)
            df_solar = pd.read_csv('BA_solar.csv',header=0)
            
            #get rid of NaNs
            a = df_wind.values
            m=np.where(np.isnan(a))
            r,c=np.shape(m)
            for i in range(0,c):
                df_wind.iloc[m[0][i],m[1][i]] = 0
            a = df_solar.values
            m=np.where(np.isnan(a))
            r,c=np.shape(m)
            for i in range(0,c):
                df_solar.iloc[m[0][i],m[1][i]] = 0    
            
            # read reduction algorithm summary and parse nodal operations
            df_summary = pd.read_excel(FN,sheet_name='Summary',header=5)
            nodes=0
            merged = {}
            N = []
            for i in range(0,len(df_summary)):
                test = df_summary.iloc[i,0]
                res = [int(i) for i in test.split() if i.isdigit()] 
                if res[1] in N:
                    pass
                else:
                    N.append(res[1])
            for n in N:
                k = []
                for i in range(0,len(df_summary)):
                    test = df_summary.iloc[i,0]
                    res = [int(i) for i in test.split() if i.isdigit()] 
                    if res[1] == n:
                        k.append(res[0])
                    else:
                        pass
                merged[n] = k
            
            ##################################
            # WIND ALLOCATION TO NODE
                       
            df_gen = pd.read_csv('ERCOT_Generators_egridhtrtadjusted.csv',header=0)
            MWMax = []
            fuel_type = []
            nums = list(df_gen['BusNum'])
            
            #add gen info to df
            for i in range(0,len(df_full)):
                bus = df_full.loc[i,'Number']
                if bus in nums:
                    MWMax.append(df_gen.loc[df_gen['BusNum']==bus,'MWMax'].values[0])
                    fuel_type.append(df_gen.loc[df_gen['BusNum']==bus,'FuelType'].values[0])
                else:
                    MWMax.append(0)
                    fuel_type.append('none')
            
            df_full['MWMax'] = MWMax
            df_full['FuelType'] = fuel_type
            
            Zone_totals = []
            
            for b in Zones:
                sample = list(df_full.loc[(df_full['ZoneName']==b) & (df_full['FuelType'] == 'WND (Wind)'),'MWMax'])
                Zone_totals.append(sum(sample))
            Z = sum(Zone_totals)
            
            Zone_totals = np.column_stack((Zones,Zone_totals))
            df_Zone_totals = pd.DataFrame(Zone_totals)
            df_Zone_totals.columns = ['Name','Total']
            
            weights = []
            for i in range(0,len(df_full)):
                area = df_full.loc[i,'ZoneName']
                if str(area) == 'nan':
                    weights.append(0)
                elif str(df_full.loc[i,'FuelType']) != 'WND (Wind)':
                    weights.append(0)
                else:        
                    W = df_full.loc[i,'MWMax']/Z
                    weights.append(W)
            df_full['Zone Wind Weight'] = weights
            
            sums = []
            for i in Zones:
                s = sum(df_full.loc[df_full['ZoneName']==i,'Zone Wind Weight'])
                sums.append(s)
            
            # selected nodes
            buses = list(df_selected['bus_i'])
            
            idx = 0
            w= 0
            T = np.zeros((8760,len(buses)))
            
            Zone_sums = np.zeros((len(Zones),1))
            
            for b in buses:
                
                #load for original node
                sample = df_full.loc[df_full['Number'] == b]
                sample = sample.reset_index(drop=True)
                name = sample['ZoneName'][0]
            
                
                if str(name) != 'nan':
            
                    abbr = 'ERCOT'
                    weight = sample['Zone Wind Weight'].values[0]
                    T[:,idx] = T[:,idx] + np.reshape(df_wind[abbr].values*weight,(8760,))
                    w += weight
                    dx = Zones.index(name)
                    Zone_sums[dx] = Zone_sums[dx] + weight
                    
                else:
                    pass
                          
                #add wind capacity from merged nodes
                try:
                    m_nodes = merged[b]
                    
                    for m in m_nodes:
                        #load for original node
                        sample = df_full.loc[df_full['Number'] == m]
                        sample = sample.reset_index(drop=True)
                        name = sample['ZoneName'][0]
                        if str(name) == 'nan':
                            pass
                        else:
                            abbr = 'ERCOT'
                            weight = sample['Zone Wind Weight']
                            w += weight  
                            dx = Zones.index(name)
                            Zone_sums[dx] = Zone_sums[dx] + weight
                            T[:,idx] = T[:,idx] + np.reshape(df_wind[abbr].values*weight.values[0],(8760,))
            
                except KeyError:
                    # print (b)
                    pass
                
                idx +=1
            
            w_buses = []
            for i in range(0,len(buses)):
                w_buses.append('bus_' + str(buses[i]))
            
            df_C = pd.DataFrame(T)
            df_C.columns = w_buses
            df_C.to_csv('nodal_wind.csv',index=None)   
            copy('nodal_wind.csv',path)
            
            
            ##################################
            # SOLAR ALLOCATION FROM BA TO NODE
                        
            Zone_totals = []
            
            for b in Zones:
                sample = list(df_full.loc[(df_full['ZoneName']==b) & (df_full['FuelType'] == 'SUN (Solar)'),'MWMax'])
                # corrected = [0 if math.isnan(x) else x for x in sample]
                Zone_totals.append(sum(sample))
            
            Z = sum(Zone_totals)
            
            Zone_totals = np.column_stack((Zones,Zone_totals))
            df_Zone_totals = pd.DataFrame(Zone_totals)
            df_Zone_totals.columns = ['Name','Total']
        
            
            weights = []
            for i in range(0,len(df_full)):
                area = df_full.loc[i,'ZoneName']
                if str(area) == 'nan':
                    weights.append(0)
                elif str(df_full.loc[i,'FuelType']) != 'SUN (Solar)':
                    weights.append(0)
                else:        
                    X = float(df_Zone_totals.loc[df_Zone_totals['Name']==area,'Total'])
                    W = df_full.loc[i,'MWMax']/Z
                    weights.append(W)
            df_full['Zone Solar Weight'] = weights
            
            sums = []
            for i in Zones:
                s = sum(df_full.loc[df_full['ZoneName']==i,'Zone Solar Weight'])
                sums.append(s)
            
            # selected nodes
            buses = list(df_selected['bus_i'])
            
            idx = 0
            w= 0
            T = np.zeros((8760,len(buses)))
            
            Zone_sums = np.zeros((28,1))
            
            for b in buses:
                
                #load for original node
                sample = df_full.loc[df_full['Number'] == b]
                sample = sample.reset_index(drop=True)
                name = sample['ZoneName'][0]
            
                
                if str(name) != 'nan':
            
                    abbr = 'ERCOT'
                    weight = sample['Zone Solar Weight'].values[0]
                    T[:,idx] = T[:,idx] + np.reshape(df_solar[abbr].values*weight,(8760,))
                    w += weight
                    dx = Zones.index(name)
                    Zone_sums[dx] = Zone_sums[dx] + weight
                    
                else:
                    pass
                          
                #add solar capacity from merged nodes
                try:
                    m_nodes = merged[b]
                    
                    for m in m_nodes:
                        #load for original node
                        sample = df_full.loc[df_full['Number'] == m]
                        sample = sample.reset_index(drop=True)
                        name = sample['ZoneName'][0]
                        if str(name) == 'nan':
                            pass
                        else:
                            abbr = 'ERCOT'
                            weight = sample['Zone Solar Weight']
                            w += weight  
                            dx = Zones.index(name)
                            Zone_sums[dx] = Zone_sums[dx] + weight
                            T[:,idx] = T[:,idx] + np.reshape(df_solar[abbr].values*weight.values[0],(8760,))
            
                except KeyError:
                    # print (b)
                    pass
                
                idx +=1
                
            
            s_buses = []
            for i in range(0,len(buses)):
                s_buses.append('bus_' + str(buses[i]))
            
            df_C = pd.DataFrame(T)
            df_C.columns = s_buses
            df_C.to_csv('nodal_solar.csv',index=None)  
            copy('nodal_solar.csv',path)
            
            
            ##############################
            # THERMAL GENERATION
            
            import re
            
            df_gens = pd.read_csv('ERCOT_Generators_egridhtrtadjusted.csv',header=0)
            df_gens = df_gens.replace('', np.nan, regex=True)
            df_gens_heat_rate = pd.read_csv('egridadjusted_ERCOT_Heat_Rates.csv',header=0)
            old_bus_num =[]
            new_bus_num = []
            NB = []
            
            old_bus_num_hr =[]
            new_bus_num_hr = []
            NB_hr = []
            
            for n in N:
                k = merged[n]
                for s in k:
                    old_bus_num.append(s)
                    new_bus_num.append(n)
            
            for i in range(0,len(df_gens)):
                OB = df_gens.loc[i,'BusNum']
                if OB in old_bus_num:
                    idx = old_bus_num.index(OB)
                    NB.append(new_bus_num[idx])
                else:
                    NB.append(OB)
            
            df_gens['NewBusNum'] = NB
            
            for i in range(0,len(df_gens_heat_rate)):
                OB = df_gens_heat_rate.loc[i,'BusNum']
                if OB in old_bus_num:
                    idx = old_bus_num.index(OB)
                    NB_hr.append(new_bus_num[idx])
                else:
                    NB_hr.append(OB)
            
            df_gens_heat_rate['NewBusNum'] = NB_hr
    
            names = list(df_gens['BusName'])
            fts = list(df_gens['FuelType'])
            names_hr = list(df_gens_heat_rate['BusName'])
            fts_hr = list(df_gens_heat_rate['BusName'])
            
            # remove numbers and spaces
            for n in names:
                i = names.index(n)
                corrected = re.sub(r'[^A-Z]',r'',n)
                f = fts[i]
                if f == 'NUC (Nuclear)':
                    f = 'Nuc'
                elif f == 'NG (Natural Gas)':
                    f = 'NG'
                elif f == 'BIT (Bituminous Coal)':
                    f = 'C'
                elif f == 'SUN (Solar)':
                    f = 'S'
                elif f == 'WAT (Water)':
                    f = 'H'
                elif f == 'WND (Wind)':
                    f = 'W'
                    
                corrected = corrected + '_' + f
                names[i] = corrected
                
            for n in names_hr:
                i = names_hr.index(n)
                corrected = re.sub(r'[^A-Z]',r'',n)
                f = fts_hr[i]
                if f == 'NUC (Nuclear)':
                    f = 'Nuc'
                elif f == 'NG (Natural Gas)':
                    f = 'NG'
                elif f == 'BIT (Bituminous Coal)':
                    f = 'C'
                elif f == 'SUN (Solar)':
                    f = 'S'
                elif f == 'WAT (Water)':
                    f = 'H'
                elif f == 'WND (Wind)':
                    f = 'W'
                    
                corrected = corrected + '_' + f
                names_hr[i] = corrected
          
            df_gens['PlantNames'] = names
            df_gens_heat_rate['PlantNames'] = names_hr            
            
            NB = df_gens['NewBusNum'].unique()
            plants = []
            caps = []
            mw_min = []
            count = 2
            nbs = []
            heat_rate = []
            f = []
            thermal = ['NG (Natural Gas)','NUC (Nuclear)','BIT (Bituminous Coal)','DFO (Distillate Fuel Oil)']
            
            for n in NB:
                sample = df_gens.loc[df_gens['NewBusNum'] == n]
                sample_hr = df_gens_heat_rate.loc[df_gens_heat_rate['NewBusNum'] == n]
                sublist = sample['PlantNames'].unique()
                for s in sublist:
                    fuel = list(sample.loc[sample['PlantNames']==s,'FuelType'])
                    if fuel[0] in thermal:
                        c = sum(sample.loc[sample['PlantNames']==s,'MWMax'].values)
                        hr = np.nanmean(sample.loc[sample['PlantNames']==s,'Heat Rate MBTU/MWH'].values)
                        if hr == np.nan or hr == 0 or hr == 'nan' or hr == '':
                            hr = np.nanmean(sample_hr.loc[sample_hr['PlantNames']==s,'Heat Rate MBTU/MWH'].values)
                        else:
                            pass
                        mn = sum(sample.loc[sample['PlantNames']==s,'MWMin'].values)
                        mw_min.append(mn)
                        caps.append(c)
                        nbs.append(n)
                        heat_rate.append(hr)
                        f.append(fuel[0])
                        if s in plants:
                            new = s + '_' + str(count)
                            plants.append(new)
                            count+=1
                        else:
                            plants.append(s)
            
            C=np.column_stack((plants,nbs))
            C=np.column_stack((C,f))
            C=np.column_stack((C,caps))
            C=np.column_stack((C,mw_min))
            C=np.column_stack((C,heat_rate))
            
            df_C = pd.DataFrame(C)
            df_C.columns = ['Name','Bus','Fuel','Max_Cap','Min_Cap','Heat_Rate']
            df_C.to_csv('thermal_gens.csv',index=None)
            copy('thermal_gens.csv',path)
                
            
            ##############################
            # HYDROPOWER
                       
            #EIA plants
            df_hydro = pd.read_csv('EIA_ERCOT_reduced_hydro_plants.csv',header=0)
            df_hydro_ts = pd.read_csv('p_mean_max_min_MW_ERCOTplants_weekly_2019.csv',header=0)
            new_hydro_nodes = []
            
            for i in range(0,len(df_hydro)):
                
                name = df_hydro.loc[i,'plant']
                new_name = re.sub(r'[^A-Z]',r'',name)
                bus = df_hydro.loc[i,'bus']
                
                if bus in old_bus_num:
                    idx = old_bus_num.index(bus)
                    new_hydro_nodes.append(new_bus_num[idx])
                    pass
                elif bus in buses:
                    new_hydro_nodes.append(bus)
                else:
                    print(name + ' Not found')
            
            # add mean/min/max by node
            H_min = np.zeros((52,len(buses)))
            H_max = np.zeros((52,len(buses)))
            H_mu = np.zeros((52,len(buses)))
            
            for i in range(0,len(df_hydro)):
                b = new_hydro_nodes[i]
                idx = buses.index(b)
                plant = df_hydro.loc[i,'plant']
                
                ts = df_hydro_ts[df_hydro_ts['plant']==plant]
                
                H_min[:,idx] += ts['min']
                H_max[:,idx] += ts['max']
                H_mu[:,idx] += ts['mean']
                
            
            # create daily time series by node
            H_min_hourly = np.zeros((365,len(buses)))
            H_max_hourly = np.zeros((365,len(buses)))
            H_mu_hourly = np.zeros((365,len(buses)))
            
            for i in range(0,len(H_min)):
                for j in range(0,len(buses)):
                    H_min_hourly[i*7:i*7+7,j] = H_min[i,j]
                    H_max_hourly[i*7:i*7+7,j] = H_max[i,j]
                    H_mu_hourly[i*7:i*7+7,j] = H_mu[i,j]*24
                    
            H_min_hourly[364,:] = H_min_hourly[363,:]
            H_max_hourly[364,:] = H_max_hourly[363,:]
            H_mu_hourly[364,:] = H_mu_hourly[363,:] 
            
            h_buses = []
            for i in range(0,len(buses)):
                h_buses.append('bus_' + str(buses[i]))
            
            H_min_df = pd.DataFrame(H_min_hourly)
            H_min_df.columns = h_buses
            H_max_df = pd.DataFrame(H_max_hourly)
            H_max_df.columns = h_buses
            H_mu_df = pd.DataFrame(H_mu_hourly) 
            H_mu_df.columns = h_buses       
            
            H_min_df.to_csv('Hydro_min.csv',index=None)
            H_max_df.to_csv('Hydro_max.csv',index=None)
            H_mu_df.to_csv('Hydro_total.csv',index=None)
            
            copy('Hydro_min.csv',path)
            copy('Hydro_max.csv',path)
            copy('Hydro_total.csv',path)
            
                
            
            #########################################
            # Generator file setup
            
            df_G = pd.read_csv('thermal_gens.csv',header=0)
            
            names = []
            typs = []
            nodes = []
            maxcaps = []
            mincaps = []
            heat_rates = []
            var_oms = []
            no_loads = []
            st_costs = []
            ramps = []
            minups = []
            mindns = []

            
            must_nodes = []
            must_caps = []
            
            for i in range(0,len(df_G)):
                
                name = df_G.loc[i,'Name']
                t = df_G.loc[i,'Fuel']
                if t == 'NG (Natural Gas)':
                    typ = 'ngcc'
                elif t == 'BIT (Bituminous Coal)':
                    typ = 'coal'
                else:
                    typ = 'nuclear'
                node = 'bus_' + str(df_G.loc[i,'Bus'])
                maxcap = df_G.loc[i,'Max_Cap']
                mincap = df_G.loc[i,'Min_Cap']
                hr_2 = df_G.loc[i,'Heat_Rate']
                
                if typ == 'ngcc':
                    var_om = 3
                    minup = 4
                    mindn = 4
                    ramp = maxcap
                else:
                    var_om = 4
                    minup = 12
                    mindn = 12
                    ramp = 0.33*maxcap
                
                st_cost = 70*maxcap
                no_load = 3*maxcap
                
                if typ != 'nuclear':
                    
                    names.append(name)
                    typs.append(typ)
                    nodes.append(node)
                    maxcaps.append(maxcap)
                    mincaps.append(mincap)
                    var_oms.append(var_om)
                    no_loads.append(no_load)
                    st_costs.append(st_cost)
                    ramps.append(ramp)
                    minups.append(minup)
                    mindns.append(mindn)
                    heat_rates.append(hr_2)

                    
                else:
                    
                    must_nodes.append(node)
                    must_caps.append(maxcap)
                
            
            # wind
            
            df_W = pd.read_csv('nodal_wind.csv',header=0)
            buses = list(df_W.columns)
            for n in buses:
                
                if sum(df_W[n]) > 0:
                    name = n + '_WIND'
                    maxcap = 100000
                    names.append(name)
                    typs.append('wind')
                    nodes.append(n)
                    maxcaps.append(maxcap)
                    mincaps.append(0)
                    var_oms.append(0)
                    no_loads.append(0)
                    st_costs.append(0)
                    ramps.append(0)
                    minups.append(0)
                    mindns.append(0) 
                    heat_rates.append(0)
               
            
            # solar
            
            df_S = pd.read_csv('nodal_solar.csv',header=0)
            buses = list(df_S.columns)
            for n in buses:
                if sum(df_S[n]) > 0:
                    name = n + '_SOLAR'
                    maxcap = 100000
                    names.append(name)
                    typs.append('solar')
                    nodes.append(n)
                    maxcaps.append(maxcap)
                    mincaps.append(0)
                    var_oms.append(0)
                    no_loads.append(0)
                    st_costs.append(0)
                    ramps.append(0)
                    minups.append(0)
                    mindns.append(0)   
                    heat_rates.append(0)
 
            
            # hydro
            
            df_H = pd.read_csv('Hydro_max.csv',header=0)
            buses = list(df_H.columns)
            for n in buses:
                if sum(df_H[n]) > 0:
                    name = n + '_HYDRO'
                    maxcap = max(df_H[n])
                    names.append(name)
                    typs.append('hydro')
                    nodes.append(n)
                    maxcaps.append(maxcap)
                    mincaps.append(0)
                    var_oms.append(1)
                    no_loads.append(1)
                    st_costs.append(1)
                    ramps.append(maxcap)
                    minups.append(0)
                    mindns.append(0)   
                    heat_rates.append(0)
 
            
            df_genparams = pd.DataFrame()
            df_genparams['name'] = names
            df_genparams['typ'] = typs
            df_genparams['node'] = nodes
            df_genparams['maxcap'] = maxcaps

            df_genparams['heat_rate'] = heat_rates
            df_genparams['mincap'] = mincaps
            df_genparams['var_om'] = var_oms
            df_genparams['no_load'] = no_loads
            df_genparams['st_cost'] = st_costs
            df_genparams['ramp'] = ramps
            df_genparams['minup'] = minups
            df_genparams['mindn'] = mindns
            
            df_genparams.to_csv('data_genparams.csv',index=None)
            copy('data_genparams.csv',path)
            
            df_must = pd.DataFrame()
            for i in range(0,len(must_nodes)):
                n = must_nodes[i]
                df_must[n] = [must_caps[i]]
            df_must.to_csv('must_run.csv',index=None)
            copy('must_run.csv',path)
            

            ######
            # create gen-to-bus matrix
            
            df = pd.read_csv('data_genparams.csv',header=0)
            gens = list(df.loc[:,'name'])
            
            df_nodes = pd.read_excel(FN, sheet_name = 'Bus', header=0)
            all_nodes = list(df_nodes['bus_i'])
            for i in range(0,len(all_nodes)):
                all_nodes[i] = 'bus_' + str(all_nodes[i])
            
            A = np.zeros((len(gens),len(all_nodes)))
            
            # for i in range(0,len(gens)):
            #     node = df.loc[i,'node']
            #     n_i = all_nodes.index(node)
            #     A[i,n_i] = 1
            
            df_A = pd.DataFrame(A)
            df_A.columns = all_nodes
            df_A['name'] = gens
            df_A.set_index('name',inplace=True)
            
            for i in range(0,len(gens)):
                node = df.loc[i,'node']
                # print(node)
                g = gens[i]
                df_A.loc[g,node] = 1
            
            df_A.to_csv('gen_mat.csv')
            copy('gen_mat.csv',path)
            
            #####################################
            # TRANSMISSION
            
            df = pd.read_excel(FN,sheet_name = 'Branch',header=0)
            
            # eliminate repeats
            lines = []
            repeats = []
            index = []
            for i in range(0,len(df)):
                
                t=tuple((df.loc[i,'fbus'],df.loc[i,'tbus']))
                
                if t in lines:
                    df = df.drop([i])
                    repeats.append(t)
                    r = lines.index(t)
                    i = index[r]
                    df.loc[i,'rateA'] += df.loc[i,'rateA']
                else:
                    lines.append(t)
                    index.append(i)
            
            df = df.reset_index(drop=True)
                
            sources = df.loc[:,'fbus']
            sinks = df.loc[:,'tbus']
            combined = np.append(sources, sinks)
            df_combined = pd.DataFrame(combined,columns=['node'])
            unique_nodes = df_combined['node'].unique()
            unique_nodes.sort()
            
            A = np.zeros((len(df),len(unique_nodes)))
            
            df_line_to_bus = pd.DataFrame(A)
            df_line_to_bus.columns = unique_nodes
            
            negative = []
            positive = []
            lines = []
            ref_node = 0
            reactance = []
            limit = []
            
            for i in range(0,len(df)):
                s = df.loc[i,'fbus']
                k = df.loc[i,'tbus']
                line = str(s) + '_' + str(k)
                if s == df.loc[0,'fbus']: 
                    lines.append(line)
                    positive.append(s)
                    negative.append(k)
                    df_line_to_bus.loc[ref_node,s] = 1
                    df_line_to_bus.loc[ref_node,k] = -1
                    reactance.append(df.loc[i,'x'])
                    MW = ((1/df.loc[i,'x'])*100) + T_p_new
                    limit.append(MW)
                    ref_node += 1
                elif k == df.loc[0,'fbus']:      
                    lines.append(line)
                    positive.append(k)
                    negative.append(s)
                    df_line_to_bus.loc[ref_node,k] = 1
                    df_line_to_bus.loc[ref_node,s] = -1
                    reactance.append(df.loc[i,'x'])
                    MW = ((1/df.loc[i,'x'])*100) + T_p_new
                    limit.append(MW)
                    ref_node += 1
                    
            for i in range(0,len(df)):
                s = df.loc[i,'fbus']
                k = df.loc[i,'tbus']
                line = str(s) + '_' + str(k)
                if s != df.loc[0,'fbus']:
                    if k != df.loc[0,'fbus']:
                        lines.append(line)
                        
                        if s in positive and k in negative:
                            df_line_to_bus.loc[ref_node,s] = 1
                            df_line_to_bus.loc[ref_node,k] = -1
                        
                        elif k in positive and s in negative:
                            df_line_to_bus.loc[ref_node,k] = 1
                            df_line_to_bus.loc[ref_node,s] = -1
                            
                        elif s in positive and k in positive:
                            df_line_to_bus.loc[ref_node,s] = 1
                            df_line_to_bus.loc[ref_node,k] = -1
                        
                        elif s in negative and k in negative:   
                            df_line_to_bus.loc[ref_node,s] = 1
                            df_line_to_bus.loc[ref_node,k] = -1
                            
                        elif s in positive:
                            df_line_to_bus.loc[ref_node,s] = 1
                            df_line_to_bus.loc[ref_node,k] = -1
                            negative.append(k)
                        elif s in negative:
                            df_line_to_bus.loc[ref_node,k] = 1
                            df_line_to_bus.loc[ref_node,s] = -1   
                            positive.append(k)
                        elif k in positive:
                            df_line_to_bus.loc[ref_node,k] = 1
                            df_line_to_bus.loc[ref_node,s] = -1  
                            negative.append(s)
                        elif k in negative:
                            df_line_to_bus.loc[ref_node,s] = 1
                            df_line_to_bus.loc[ref_node,k] = -1 
                            positive.append(s)
                        else:
                            positive.append(s)
                            negative.append(k)
                            df_line_to_bus.loc[ref_node,s] = 1
                            df_line_to_bus.loc[ref_node,k] = -1
            
                        reactance.append(df.loc[i,'x'])
                        MW = ((1/df.loc[i,'x'])*100) + T_p_new
                        limit.append(MW)
                        ref_node += 1
            
            unique_nodes = list(unique_nodes)
            for i in range(0,len(unique_nodes)):
                unique_nodes[i] = 'bus_' + str(unique_nodes[i])
            df_line_to_bus.columns = unique_nodes
            
            for i in range(0,len(lines)):
                lines[i] = 'line_' + lines[i]
                
            df_line_to_bus['line'] = lines
            df_line_to_bus.set_index('line',inplace=True)
            df_line_to_bus.to_csv('line_to_bus.csv')
            copy('line_to_bus.csv',path)
            
            
            df_line_params = pd.DataFrame()
            df_line_params['line'] = lines
            df_line_params['reactance'] = reactance
            df_line_params['limit'] = limit 
            df_line_params.to_csv('line_params.csv',index=None)
            copy('line_params.csv',path)
            
            #####################################
            # FUEL PRICES
            
            # Natural gas prices
            NG_price = pd.read_csv('gas_prices.csv', header=0,index_col=None)
            buses = list(df_selected['bus_i'])
            for bus in buses:
                
                # selected_node_BA = df_full.loc[df_full['Number']==bus,'NAME'].values[0]
                specific_node_NG_price = NG_price.loc[:,'HenryHub'].copy()
                
                if buses.index(bus) == 0:
                    NG_prices_all = specific_node_NG_price.copy()
                else:
                    NG_prices_all = pd.concat([NG_prices_all,specific_node_NG_price], axis=1)
            
            Fuel_buses = []
            for i in range(0,len(buses)):
                Fuel_buses.append('bus_' + str(buses[i]))
            
            NG_prices_all.columns = Fuel_buses
            
            # Coal prices
            Coal_price = pd.read_csv('coal_prices.csv', header=0)
    
            for bus in buses:
                
                # selected_node_state = df_full.loc[df_full['Number']==bus,'STATE'].values[0]
                specific_node_coal_price = Coal_price.loc[:,'TX'].copy()
                
                if buses.index(bus) == 0:
                    Coal_prices_all = specific_node_coal_price.copy()
                else:
                    Coal_prices_all = pd.concat([Coal_prices_all,specific_node_coal_price], axis=1)
            
            Coal_prices_all.columns = Fuel_buses
            
            # getting generator based fuel prices
            
            thermal_gens_info = df_genparams.loc[(df_genparams['typ']=='ngcc') | (df_genparams['typ']=='coal')].copy()
            thermal_gens_names = [*thermal_gens_info['name']]

            for ind, row in thermal_gens_info.iterrows():
                
                if row['typ'] == 'ngcc':
                    gen_fuel_price = NG_prices_all.loc[:, row['node']].copy() 
                elif row['typ'] == 'coal':
                    gen_fuel_price = Coal_prices_all.loc[:, row['node']].copy() 
                else:
                    pass
                
                if thermal_gens_names.index(row['name']) == 0:
                    Fuel_prices_all = gen_fuel_price.copy()
                else:
                    Fuel_prices_all = pd.concat([Fuel_prices_all,gen_fuel_price], axis=1)
                    
            Fuel_prices_all.columns = thermal_gens_names
            
            Fuel_prices_all.to_csv('Fuel_prices.csv',index=None)
            copy('Fuel_prices.csv',path)       

            
            
            #copy other files
            w = 'wrapper' + UC + '.py'
            milp = 'ERCOT_MILP' + UC + '.py'
            lp = 'ERCOT_LP' + UC + '.py'
            
            copy(w,path)
            copy('ERCOTDataSetup.py',path)
            
            if UC == '_simple':
                copy('ERCOT' + UC + '.py',path)
            else:          
                copy(milp,path)
                copy(lp,path)

            
            copy('ercot2019_lostcap_v3.csv',path)
            #importing a function created in another script to generate a dictionary from the data_genparams file
            from dict_creator import dict_funct
            df_loss_dict=dict_funct(df_genparams)
            #save the dictionary as a .npy file
            np.save('df_dict2.npy', df_loss_dict)
            copy('df_dict2.npy',path)
            
    
