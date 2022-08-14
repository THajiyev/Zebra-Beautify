import requests
import concurrent.futures
import re

class Zebra:

    def __init__(self, key):
        self.headers = {'X-TBA-Auth-Key':key}
    
    def get_link(self, match_key):
        baseURL = 'https://www.thebluealliance.com/api/v3/'
        url=baseURL+"match/"+match_key+"/zebra_motionworks"
        return url

    # Output: competition level, match number
    def get_info(self, event, match_key):
        #match keys for qualification matches have a different format
        if match_key.startswith(event+"_qm"):
            return ("qm", match_key[len(event+"_qm"):])
        else:
            return (re.sub(r'\d', ' ', match_key[len(event)+1:]).split(" ")[0], match_key[match_key.rindex("m")+1:])
    
    # Output: success, match_data
    def get_tba_data(self, match_key):
        data = requests.get(url=self.get_link(match_key), headers=self.headers).json()
        if data is None:
            return True, []
        if 'Error' in data:
            return False, []
        return True, data
    
    def get_match_data(self, match_key, max_data_loss):
        data = {}
        alliances = ['red', 'blue']
        success, match_data = self.get_tba_data(match_key)
        if not success:
            return data
        if match_data!=[]:
            times = match_data["times"]
            for color in alliances:
                alliance_data = match_data['alliances'][color]
                for team_data in alliance_data:
                        x_coordinates = team_data["xs"]
                        y_coordinates = team_data["ys"]
                        if x_coordinates[0:max_data_loss+1].count(None)<=max_data_loss and  y_coordinates[0:max_data_loss+1].count(None)<=max_data_loss:
                            starting_time = times[x_coordinates.index(next(item for item in x_coordinates if item is not None))]
                            x_coordinates = list(filter((None).__ne__, team_data["xs"]))
                            y_coordinates = list(filter((None).__ne__, team_data["ys"]))
                            data[team_data["team_key"]]={"alliance":color, "starting_time":starting_time,"x":x_coordinates, "y":y_coordinates}
        return match_key, data

    def get_event_zebra(self, event, max_data_loss=10):
        threads = []
        data = {}
        matches = requests.get(url='https://www.thebluealliance.com/api/v3/event/'+event+'/matches/keys', headers=self.headers).json() 
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for match_key in matches:
                thread = executor.submit(self.get_match_data, match_key, max_data_loss)
                threads.append(thread)
        for thread in threads:
            match_key, new_data = thread.result()
            competition_level, match_number = self.get_info(event, match_key)
            for team_number in new_data.keys():
                if team_number not in data.keys():
                    data[team_number]={}
                if competition_level not in data[team_number].keys():
                    data[team_number][competition_level]={}
                data[team_number][competition_level][match_number]=new_data[team_number]
        return data
    
    def get_match_zebra(self, match_key, max_data_loss=10):
        _, match_data = self.get_match_data(match_key, max_data_loss)
        return match_data
    