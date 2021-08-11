# Python implementation of the SIMPLE crop model by T Moon, GHPF Lab of SNU.
# Zhao C, Liu B, Xiao L, Hoogenboom G, Boote KJ, Kassie BT, Pavan W, Shelia V, Kim KS, Hernandez-Ochoa IM et al. (2019) A SIMPLE crop model. Eur J Agron 104:97-106

import numpy as np

# The environment data were assumed to have one-hour interval.
def env_feeder(env_df):
    input_env = env_df.values # pd.DataFrame to np.array
    pass
        

# Input for running crop should be a vector (temperature, radiation, CO2, ... etc at each day)
class Crop:
    def __init__(self, crop_params, soil_params):
        # Crop parameters
        self.T_sum        = crop_params[0]
        self.HI           = crop_params[1]
        self.I_50A        = crop_params[2]
        self.I_50B        = crop_params[3]
        self.T_base       = crop_params[4]
        self.T_opt        = crop_params[5]
        self.RUE          = crop_params[6]
        self.I_50maxH     = crop_params[7]
        self.I_50maxW     = crop_params[8]
        self.T_heat       = crop_params[9]
        self.T_ext        = crop_params[10]
        self.S_CO2        = crop_params[11]
        self.S_water      = crop_params[12]
        self.fSolar_max   = 0.8
        
        # Soil parameters
        self.AWC          = soil_params[0]
        self.RCN          = soil_params[1]
        self.DDC          = soil_params[2]
        self.RZD          = soil_params[3]
        
        # Variables
        self.days         = 0    # days after sowing, planting, ... whatever.
        self.TT           = 0    # cumulative mean temperature
        self.biomass_cum  = 0    # cumulative biomass
        self.yields        = 0
        
    def phenology(self, T_max, T_min):
        T_mean = (T_max + T_min) / 2
        if T_mean > self.T_base:
            dTT = T_mean - self.T_base
        else:
            dTT = 0        
        self.TT += dTT
        
        return self.TT
        
        
    def growth(self, T_max, T_min, rad, CO2):
        T_mean = (T_max + T_min)/2
        # fSolar calculation
        fSolar = min(self.fSolar_max/(1 + np.exp(-0.01*(self.TT - self.I_50A))),
                     self.fSolar_max/(1 + np.exp(0.01*(self.TT - (self.T_sum - self.I_50B)))))
        
        # f(Temp) calculation
        if T_mean < self.T_base:
            fTemp = 0
        elif T_mean >= self.T_base and T_mean < self.T_opt:
            fTemp = (T_mean - self.T_base)/(self.T_opt - self.T_base)
        else: # T_mean >= self.T_opt
            fTemp = 1
        
        # f(heat) calculation
        if T_max <= self.T_heat:
            fHeat = 1
        elif T_max > self.T_heat and T_max <= self.T_ext:
            fHeat = 1 - (T_max - self.T_heat)/(self.T_ext - self.T_heat)
        else: # T_max > self.T_ext
            fHeat = 0
                
        # f(CO2) calculation
        if CO2 >= 350 and CO2 < 700:
            fCO2 = 1 + self.S_CO2*(CO2 - 350)
        elif CO2 > 700:
            fCO2 = 1 + self.S_CO2*350
            
        # f(Water) calculation
        # ARID = 1 - min(self.ET_0*self.PAW)/self.ET_0
        ARID = 0 # No information about ET_0 and PAW
        fWater = 1 - self.S_water*ARID
        
        # Updating I_50B with f(Heat) and f(Water)
        self.I_50B += self.I_50maxH*(1 - fHeat)
        self.I_50B += self.I_50maxW*(1 - fWater)
        
        biomass_rate = rad*fSolar*self.RUE*fCO2*fTemp*min(fHeat, fWater)
        self.biomass_cum += biomass_rate

        return fSolar, self.biomass_cum
    
    
    def run(self, weather_data):
        TTs = []
        solar = []
        biomass = []
        days = []
        for daily_weather in weather_data:
            TTs.append(self.phenology(daily_weather[0], daily_weather[1]))
            _, __ = self.growth(daily_weather[0], daily_weather[1], daily_weather[2], daily_weather[3])
            solar.append(_)
            biomass.append(__)
            
            self.days += 1
            days.append(self.days)
        
        self.yields = self.biomass_cum*self.HI
        
        return self.yields, TTs, biomass, days, solar