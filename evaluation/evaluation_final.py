# -*- coding: utf-8 -*-
"""
Created on Sun Dec 29 14:58:37 2019

@author: windows
"""

#To use this evaluation code, use this command in command line
#python evaluation_final.py mode actualResult.json recommendResult.json output.txt
#ex python evaluation_final.py allMatch actual//actual.json out//recommendResult.json eval.txt

import json
import pandas as pd
import sys
from datetime import datetime
import operator as op
from functools import reduce
import math
import xlsxwriter 
import matplotlib.pyplot as plt 
import numpy as np
data = []
actual = []

def saveTeamSizeDistribution(size, outfigname):
    sizearray = np.array(size)
    plt.hist(sizearray ) 
    plt.ylabel('freq')
    plt.savefig(outfigname)



def intersection(lst1, lst2): 
    lst3 = list(set(lst1) & set(lst2))
    return lst3 
def teamToSet(team):
    return team['developer']+team['tester']+team['reviewer']+team['integrator']

#return the ratio of match in each predict result (1 recommend team) 1 is maximum and 0 is not matched
def compareMem(actual, predict):
    summatch = 0
    match = 0
    for k, v in predict.items():
        if len(v) !=0 :
            if k.startswith('dev'):
#                 print(len(intersection(actual['developer'], v)))
#                 print(actual['developer'], v)
                summatch = summatch + len(intersection(actual['developer'], v))

            elif k.startswith('tester'):
#                 print(len(intersection(actual['tester'], v)))
#                 print(actual['tester'], v)
                summatch = summatch + len(intersection(actual['tester'], v))
            elif k.startswith('reviewer'):
#                 print(len(intersection(actual['reviewer'], v)))
#                 print(actual['reviewer'], v)
                summatch = summatch + len(intersection(actual['reviewer'], v))
            elif k.startswith('integrator'):
                summatch = summatch + len(intersection(actual['integrator'], v))
        if summatch == (len(actual['developer'])+ len(actual['tester'])+len(actual['reviewer'])+len(actual['integrator'])):
            match = 1
        else:
            match = summatch/(len(actual['developer'])+ len(actual['tester'])+len(actual['reviewer'])+len(actual['integrator']))
    return match

#Calculate precision at rank K
def pak(checkMatch):
    #precision
    sump = 0
    precision = []
    for i in range(len(checkMatch)):
        sump = sump+checkMatch[i]
        precision.append(sump/(i+1))
    return precision

def pakPartialMatch(teamSize, checkMatch):
     #precision
     sump = 0
     precision = []
     for i in range(len(checkMatch)):
         sump = sump+checkMatch[i]
 #         print("Precision at ",i+1," = ", sump/(teamSize * (i+1)))
 #         print("----------------------------------------------------------------")
         precision.append(sump/(teamSize * (i+1)))
     return precision

def MAP(checkMatch, pak):
    checkMatch = checkMatch[:10]
    mapval = 0
    if checkMatch.count(1) != 0:
        index = [i for i,v in enumerate(checkMatch) if v == 1]
        for i in index:
            mapval = mapval + pak[i]
            
        mapval = mapval/checkMatch.count(1)
        
    return mapval

def averagePrecision(precision):
    n = len(precision)
    avgPrecision = []
    length = []
    
    for i in precision:
        length.append(len(i))
    
    avgPrecisionRank = [0 for i in range(max(length))]
    for i in precision:
        for j in range(len(i)):
            avgPrecisionRank[j] = avgPrecisionRank[j] + i[j]
    
    for k in range(max(length)):
        avgPrecisionRank[k] = avgPrecisionRank[k]/n
        avgPrecision.append(avgPrecisionRank[k])
        
    return avgPrecision

def mrr(result):
    mrr = 0
    sumrank = 0
    for i in result:
        try:
            relatedRank = i.index(1) + 1
            if(relatedRank!=0):
                sumrank = sumrank + 1/relatedRank
        except:
            sumrank = sumrank + 0
    return sumrank/len(result)

def fact(n): 
    res = 1
    for i in range(2, n+1): 
        res = res * i 
    return res

def ncr(n, r):
    return (fact(n) / (fact(r) * fact(n - r))) 

def bpref(result, checkMatch):

    #find all relevant    
    team = result[0]['team']
    teamSize = len(team['developer'])+len(team['integrator'])+len(team['reviewer'])+len(team['tester'])
    
    numRelated = ncr(int(teamSize), math.floor(teamSize/2))
    b = 0
    summatch = 0
    notmatch = 0
    for i in range(len(checkMatch)):
        if checkMatch[i] == 1:   #relevant
            summatch  = summatch + (1-(notmatch/numRelated))
        else: 
            notmatch = notmatch + 1
    b = (1/numRelated) * summatch      
    
    return b
      
def meanRank(result):
    mr = 0
    matchPredict = 0  #consider only predict result that contains 1
    for res in result:
        try:
            rank = res.index(1) + 1
            matchPredict += 1
        except:
            rank = 0
        mr = mr + rank
    if matchPredict == 0:
        return 0
    else:
        return mr/matchPredict
    
def meanRankAll(result):
    mr = 0
    matchPredict = 0  #consider only predict result that contains 1
    for res in result:
        try:
            rank = res.index(1) + 1
            matchPredict += 1
        except:
            rank = 101 #in case 100
        mr = mr + rank
        
    return mr/len(result)

def hitAt10(result):
    hit = []
    for res in result:
        if len(res)>=10:
            hit.append(res[0:10].count(1))
        else:
            hit.append(res.count(1))

    # return sum(hit)/len(hit) 
    return hit

def hitAt100(result):
    hit = []
    for res in result:
        if len(res)>=100:
        
            hit.append(res[0:100].count(1))
        else:
            hit.append(res.count(1))
    # return sum(hit)/len(hit)   
    return hit

#The whole team match
def exactMatch(actual, result):
    checkMatch = []
    for res in result:
        team = res['team']
        sim = compareMem(actual, team)
        if sim == 1:
            checkMatch.append(sim)
        else: 
            checkMatch.append(0)
            
    #generate not match team incase result is less than 100 team        
    if len(result) < 100:
        for i in range(100-len(result)):
            checkMatch.append(0)
            
    return checkMatch

#if 50 percent of members match, then this team is match (1)
def halfMatch(actual, result):
    checkMatch = []
    for res in result:
        team = res['team']
        sim = compareMem(actual, team)
        if sim >= 0.5:
            checkMatch.append(1)
        else: 
            checkMatch.append(0)
            
    #generate not match team incase result is less than 100 team        
    if len(result) < 100:
        for i in range(100-len(result)):
            checkMatch.append(0)
            
    return checkMatch

def partialMatch(actual, result):
    checkMatch = []
    for res in result:
        team = res['team']
        teamSize = len(team['developer'])+len(team['integrator'])+len(team['reviewer'])+len(team['tester'])
        matchRatio = compareMem(actual, team)
        checkMatch.append(matchRatio * teamSize)
        
    #generate not match team incase result is less than 100 team        
    if len(result) < 100:
        for i in range(100-len(result)):
            checkMatch.append(0)
    return checkMatch

def individual(actual, result):     

    match = []
    static = {'developer': [], 'reviewer':[], 'tester':[], 'integrator':[]}
    
    static['developer'] = intersection(result[0]['team']['developer'], result[1]['team']['developer'])
    static['tester'] = intersection(result[0]['team']['tester'], result[1]['team']['tester'])
    static['reviewer'] = intersection(result[0]['team']['reviewer'], result[1]['team']['reviewer'])
    static['integrator'] = intersection(result[0]['team']['integrator'], result[1]['team']['integrator'])
    
    recRole = ''
    if len(static['developer']) != len(actual['developer']):
        recRole = 'developer'
        
    elif len(static['tester']) != len(actual['tester']):
        recRole = 'tester'
        
    elif len( static['reviewer']) != len(actual['reviewer']):
        recRole = 'reviewer'
        
    elif len(static['integrator']) != len(actual['integrator']):
        recRole = 'integrator'
    
    person = [i for i in actual[recRole] if i not in static[recRole]]

    for predict in result:
        recommend = [i for i in predict['team'][recRole] if i not in static[recRole]]
#        print('True:' + str(person) + ' Rec:'+str(recommend) + str(predict['team'][recRole]))
        if len(set(person + recommend)) == 1:
            match.append(1)
        else:
            match.append(0)
#    print(match)
    return match        

def checkIndividual(recRole,actual, result):     

    match = []
    # static = {'developer': [], 'reviewer':[], 'tester':[], 'integrator':[]}
    static = intersection(result[0]['team'][recRole], result[1]['team'][recRole])
 
    person = [i for i in actual[recRole] if i not in static]
    
    for predict in result:
        recommend = [i for i in predict['team'][recRole] if i not in static]
        if len(set(person + recommend)) == 1:
            match.append(1)
        else:
            match.append(0)
    
    if len(match)< 100:
        for i in range(100-len(match)):
            match.append(0)

    return match        
    

def evaluation(mode, actualFilename, resultFilename,outfile, workbook):
    with open(resultFilename) as json_file:
        data = json.load(json_file)
        result = pd.DataFrame(data)
    with open(actualFilename) as json_file:
        data2 = json.load(json_file)
        actual = pd.DataFrame(data2)
        actual.set_index('issue',inplace=True)
        
    delayissue = set()
    if len(actual) !=0:
        
        allMatch = [] #Store list of comparing result of every issue
        precision = []
        bprefResult = []
        
        maprecision = []
        
        avgMatchTeam = 0
        countMatch = 0

        matchTeamSize = []
        
        for i, r in result.iterrows():
            
            if r['issue'] not in delayissue:
            
                actualTeam = actual.loc[r['issue']]['r'][0]['team']
                    
                teamSize = len(actualTeam['developer'])+len(actualTeam['integrator'])+len(actualTeam['reviewer'])+len(actualTeam['tester']) 
                if mode == 'exactMatch':
                    checkMatch = exactMatch(actualTeam, r['r'])
                    
                    if checkMatch.count(1) != 0:
                        
                        avgMatchTeam = avgMatchTeam + teamSize+1
                        countMatch = countMatch +1
                        matchTeamSize.append(teamSize+1)
                   
                    allMatch.append(checkMatch)
                    p = pak(checkMatch)
                    precision.append(p)
                    maprecision.append(MAP(checkMatch, p))
                    
                elif mode == 'halfMatch':
                    checkMatch = halfMatch(actualTeam, r['r'])
                    if checkMatch.count(1) > int(teamSize/2):
                        avgMatchTeam = avgMatchTeam + teamSize+1
                        countMatch = countMatch +1
                        
                    allMatch.append(checkMatch)
                    p = pak(checkMatch)
                    precision.append(p)
                    maprecision.append(MAP(checkMatch, p))
                    bprefResult.append(bpref(r['r'], checkMatch))
            
                elif mode == 'partialMatch':
                    checkMatch = partialMatch(actualTeam, r['r'])
                    
                    if checkMatch.count(0) != teamSize:
                        avgMatchTeam = avgMatchTeam + teamSize + 1
                        countMatch = countMatch +1
                        
                    allMatch.append(checkMatch)
                    p = pakPartialMatch(teamSize, checkMatch)
                    precision.append(p)
                    maprecision.append(MAP(checkMatch, p))
                    
                elif mode == 'individual':
                    recRole = 'reviewer'
                    checkMatch = checkIndividual(recRole,actualTeam, r['r'])
                    
                    if checkMatch.count(1) != 0:
                        avgMatchTeam = avgMatchTeam + teamSize+1
                        countMatch = countMatch +1
                        matchTeamSize.append(teamSize+1)
                        
                    allMatch.append(checkMatch)
                    p = pak(checkMatch)
                    precision.append(p)
                    maprecision.append(MAP(checkMatch, p))
                
        #save precision values
        # data = pd.DataFrame(list(zip(precision, maprecision)), columns =['precision', 'maprecision'])
        # csvfile = outfile.replace('.txt', '_'+mode+'_precision'+'.csv')
        # data.to_csv(csvfile)
        
        #consider issue by issue (each issue has many teams) 
        # file = open(outfile,"a") 
        precisioncol = [ 'P @ '+str(i+1) for i in range(10)]
        
        print('-------------------------evaluation summary-------------------------')
        
#        file.write('\n match result: '+str(allMatch)+'\n')
        if mode == 'exactMatch':
            
            mrrval = mrr(allMatch)
            hit_temp = hitAt10(allMatch)
            hit = sum(hit_temp)/len(hit_temp)
            hit100_temp = hitAt100(allMatch)
            hit100 = sum(hit100_temp)/len(hit100_temp)
            MR = meanRank(allMatch)
            MRall= meanRankAll(allMatch)
            avgTeamSize = avgMatchTeam/countMatch
            MAPval = sum(maprecision)/len(maprecision)
            precisionList = averagePrecision(precision)
            
#             In exact match, only bpref is available
            print('---------------------------Exact Match---------------------------')
            print('MRR: ', mrrval)
            print('hit at 10: ', hit)
            print('hit at 100: ', hit100)
            print('MR: ', MR)
            print('MR of all recommendation: ', MRall)
            print('Size of Match team: ', avgTeamSize)
            print('Number of Match team: ', countMatch)
            print('MAP: ', MAPval)
            print('average precision at K: ', precisionList)
                        
            worksheet = workbook.add_worksheet('exactMatch') 
            result = [ 
                ['MRR', mrrval],   
                ['MR of hits',  MR], 
                ['MR of all',  MRall], 
                ['hit at 10',   hit],
                ['hit at 100',   hit100], 
                ['bpref', ''],
                ['avgTeamSize',avgTeamSize],
                ['MAP', MAPval]
            ] 

            for i in range(10):
                result.append([precisioncol[i], precisionList[i]])
            # Start from the first cell. Rows and 
            # columns are zero indexed. 
            
            resulttuple = tuple(result)
            row = 0
            col = 0
  
            #Iterate over the data and write it out row by row. 
            for name, score in (resulttuple): 
                worksheet.write(row, col, name) 
                worksheet.write(row, col + 1, score) 
                row += 1
                
            # img = outfile.replace('.txt', '_exact.png')
            # saveTeamSizeDistribution(matchTeamSize, img)
            
            # data = pd.DataFrame({'precision': precision,'maprecision': maprecision,'hit': hit_temp, 'hit100': hit100_temp})
            # pklfile = outfile.replace('.txt', '_'+mode+'_info'+'.pkl')
            # data.to_pickle(pklfile)
            
        elif mode == 'halfMatch':
            
            mrrval = mrr(allMatch)
            MR = meanRank(allMatch)
            MRall= meanRankAll(allMatch)
            hit_temp = hitAt10(allMatch)
            hit = sum(hit_temp)/len(hit_temp)
            hit100_temp = hitAt100(allMatch)
            hit100 = sum(hit100_temp)/len(hit100_temp)
            bprefval = sum(bprefResult)/len(bprefResult)
            avgTeamSize = avgMatchTeam/countMatch
            MAPval = sum(maprecision)/len(maprecision)
            precisionList = averagePrecision(precision)
            
            print('---------------------------Half Match---------------------------')
            print('MRR: ', mrrval)
#            print('bpref: ', bprefResult)
            print('MR: ', MR)
            print('MR of all recommendation: ', MRall)
            print('hit at 10: ', hit)
            print('hit at 100: ', hit100)
            print('avg bpref: ', bprefval)
            print('Size of Match team: ', avgTeamSize)
            print('Number of Match team: ', countMatch)
            print('MAP: ', MAPval)
            print('average precision at K: ', precisionList)
            
            worksheet = workbook.add_worksheet('halfMatch') 
            
            result = [ 
                ['MRR', mrrval],   
                ['MR of hits',  MR], 
                ['MR of all',  MRall], 
                ['hit at 10',   hit], 
                ['hit at 100',   hit100], 
                ['bpref', bprefval],
                ['avgTeamSize',avgTeamSize],
                ['MAP', MAPval]
            ] 

            for i in range(10):
                result.append([precisioncol[i], precisionList[i]])
            # Start from the first cell. Rows and 
            # columns are zero indexed. 
            
            resulttuple = tuple(result)
            row = 0
            col = 0
  
            #Iterate over the data and write it out row by row. 
            for name, score in (resulttuple): 
                worksheet.write(row, col, name) 
                worksheet.write(row, col + 1, score) 
                row += 1

            # img = outfile.replace('.txt', '_half.png')
            # saveTeamSizeDistribution(matchTeamSize, img)

            # data = pd.DataFrame({'precision': precision,'maprecision': maprecision,'hit': hit_temp, 'hit100': hit100_temp, 'bpref':bprefResult})
            # pklfile = outfile.replace('.txt', '_'+mode+'_info'+'.pkl')
            # data.to_pickle(pklfile)
            
        elif mode == 'partialMatch':
            MAPval = sum(maprecision)/len(maprecision)
            avgTeamSize = avgMatchTeam/countMatch
            precisionList = averagePrecision(precision)
            print('---------------------------Partial Match--------------------------------')
#            print('precision at K: ',precision)
            print('Size of Match team: ', avgMatchTeam/countMatch)
            print('Number of Match team: ', countMatch)
            print('MAP: ', MAPval)
            print('average precision at K: ',precisionList)
            
            worksheet = workbook.add_worksheet('partialMatch') 
            result = [ 
                ['avgTeamSize',avgTeamSize],
                ['MAP', MAPval]
            ] 

            for i in range(10):
                result.append([precisioncol[i], precisionList[i]])
            
            resulttuple = tuple(result)
            row = 0
            col = 0
  
            #Iterate over the data and write it out row by row. 
            for name, score in (resulttuple): 
                worksheet.write(row, col, name) 
                worksheet.write(row, col + 1, score) 
                row += 1
                
            # img = outfile.replace('.txt', '_partial.png')
            # saveTeamSizeDistribution(matchTeamSize, img)
            
            # data = pd.DataFrame({'precision':precision,'maprecision': maprecision})
            # pklfile = outfile.replace('.txt', '_'+mode+'_info'+'.pkl')
            # data.to_pickle(pklfile)

        
        elif mode == 'individual':
            mrrval = mrr(allMatch)
            hit_temp = hitAt10(allMatch)
            hit = sum(hit_temp)/len(hit_temp)
            hit100_temp = hitAt100(allMatch)
            hit100 = sum(hit100_temp)/len(hit100_temp)
            MR = meanRank(allMatch)
            MRall= meanRankAll(allMatch)
            avgTeamSize = avgMatchTeam/countMatch
            MAPval = sum(maprecision)/len(maprecision)
            precisionList = averagePrecision(precision)
            
#             In exact match, only bpref is available
            print('---------------------------individual Match---------------------------')
            print('MRR: ', mrrval)
            print('hit at 10: ', hit)
            print('hit at 100: ', hit100)
            print('MR: ', MR)
            print('MR of all recommendation: ', MRall)
            print('Size of Match team: ', avgTeamSize)
            print('Number of Match team: ', countMatch)
            print('MAP: ', MAPval)
            print('average precision at K: ', precisionList)
                        
            worksheet = workbook.add_worksheet('individual') 
            result = [ 
                ['MRR', mrrval],   
                ['MR of hits',  MR], 
                ['MR of all',  MRall], 
                ['hit at 10',   hit],
                ['hit at 100',   hit100], 
                ['bpref', ''],
                ['avgTeamSize',avgTeamSize],
                ['MAP', MAPval]
            ] 

            for i in range(10):
                result.append([precisioncol[i], precisionList[i]])
            # Start from the first cell. Rows and 
            # columns are zero indexed. 
            
            resulttuple = tuple(result)
            row = 0
            col = 0
  
            #Iterate over the data and write it out row by row. 
            for name, score in (resulttuple): 
                worksheet.write(row, col, name) 
                worksheet.write(row, col + 1, score) 
                row += 1
                
            img = outfile.replace('.txt', '_individual.png')
            # saveTeamSizeDistribution(matchTeamSize, img)
            
            data = pd.DataFrame({'precision': precision,'maprecision': maprecision,'hit': hit_temp, 'hit100': hit100_temp})
            # pklfile = outfile.replace('.txt', '_'+mode+'_info'+'.pkl')
            # data.to_pickle(pklfile)   
            
        # timestamp = 1545730073
        # dt_object = datetime.fromtimestamp(timestamp)
        # file.write("timestamp ="+ str(dt_object)+'\n')
        # file.close() 

def getEvaluationValue(mode, actualFilename, resultFilename,outfile):
    with open(resultFilename) as json_file:
        data = json.load(json_file)
        result = pd.DataFrame(data)
        #result = result[100:]

    with open(actualFilename) as json_file:
        data2 = json.load(json_file)
        actual = pd.DataFrame(data2)
        actual.set_index('issue',inplace=True)
        
    if len(actual) !=0:
        
        allMatch = [] #Store list of comparing result of every issue
        precision = []
        bprefResult = []
        
        for i, r in result.iterrows():
            actualTeam = actual.loc[r['issue']]['r'][0]['team']
            if mode == 'exactMatch':
                checkMatch = exactMatch(actualTeam, r['r'])
#                 pak(checkMatch)
                allMatch.append(checkMatch)
                precision.append(pak(checkMatch))
                
            elif mode == 'halfMatch':
                checkMatch = halfMatch(actualTeam, r['r'])
#                 pak(checkMatch)
                allMatch.append(checkMatch)
                precision.append(pak(checkMatch))
                bprefResult.append(bpref(r['r'], checkMatch))
        
            elif mode == 'partialMatch':
                checkMatch = partialMatch(actualTeam, r['r'])
                teamSize = len(actualTeam['developer'])+len(actualTeam['integrator'])+len(actualTeam['reviewer'])+len(actualTeam['tester']) 
                allMatch.append(checkMatch)
                precision.append(pakPartialMatch(teamSize, checkMatch))
                
            elif mode == 'individual':
                checkMatch = individual(actualTeam, r['r'])
                allMatch.append(checkMatch)
                precision.append(pak(checkMatch))

        if mode == 'exactMatch':
            return {'MRR':str(mrr(allMatch)),'MR': meanRank(allMatch),'hit at 10': hitAt10(allMatch),'pre': averagePrecision(precision) }
 
        elif mode == 'halfMatch':
            return {'MRR':str(mrr(allMatch)),'MR': meanRank(allMatch),'MRall': meanRankAll(allMatch),'hit at 10': hitAt10(allMatch),'bpref':sum(bprefResult)/len(bprefResult),'pre': averagePrecision(precision) }

        elif mode == 'partialMatch':
            return {'MRR':'','MR': '','hit at 10': '','pre': averagePrecision(precision) }

        elif mode == 'individual':
            return {'MRR':str(mrr(allMatch)),'MR': meanRank(allMatch),'MRall': meanRankAll(allMatch),'hit at 10': hitAt10(allMatch),'pre': averagePrecision(precision) }

def main_eval(mode, actual, predict, outfile):
  
    if 1==1:   
        if mode == 'allMatch':
            excel = outfile.replace('.txt', '.xlsx')
            workbook = xlsxwriter.Workbook(excel) 
            evaluation('exactMatch',actual ,predict, outfile, workbook )
            evaluation('halfMatch',actual ,predict, outfile, workbook)
            evaluation('partialMatch',actual ,predict, outfile, workbook)  
            workbook.close()
        else:
            excel = outfile.replace('.txt', '.xlsx')
            workbook = xlsxwriter.Workbook(excel) 
            evaluation(mode,actual ,predict, outfile, workbook)
            workbook.close()
      
      
if __name__== "__main__":
  
    if len(sys.argv) != 5:   
        workbook = xlsxwriter.Workbook('test.xlsx') 
        evaluation('exactMatch','actual//actual.json' ,'out//recommendResult.json', 'evaluationResult.txt',workbook)
        #evaluation('halfMatch','actual//actual.json' ,'out//recommendResult.json')
        #evaluation('partialMatch','actual//actual.json' ,'out//recommendResult.json')  
        workbook.close()
    else:
        mode = sys.argv[1]
        actual = sys.argv[2]
        predict = sys.argv[3]
        outfile = sys.argv[4]
        if mode == 'allMatch':
            excel = outfile.replace('.txt', '.xlsx')
            workbook = xlsxwriter.Workbook(excel) 
            evaluation('exactMatch',actual ,predict, outfile, workbook )
            evaluation('halfMatch',actual ,predict, outfile, workbook)
            evaluation('partialMatch',actual ,predict, outfile, workbook)  
            workbook.close()
        else:
            excel = outfile.replace('.txt', '.xlsx')
            workbook = xlsxwriter.Workbook(excel) 
            evaluation(mode,actual ,predict, outfile, workbook)
            workbook.close()
            
# workbook = xlsxwriter.Workbook('test.xlsx') 
# evaluation('exactMatch', 'actual//new//actual_team_atlassian.json','out//output//winnotwin//atlassian//output_random_atlassian.json','output_random_atlassian_testexcel.txt', workbook)
# #evaluation('partialMatch', 'actual//actual_team_moodle.json','out//Moodle//v1_new//output_our_moodle.json','eval_result//Moodle//v1_new//output_haibin_moodle_testexcel.txt', workbook)
# workbook.close()
            
# for test filter
            
# dataset = ['moodle','apache','atlassian']   

# for d in dataset:
#     main_eval('exactMatch', 'actual/new/actual_team_'+d+'.json', 'out/output/hitmiss/'+d+'/output_our_hitnohit_'+d+'.json', 'eval_our_'+d+'_getTeam.txt')

#dataset = ['moodle','apache','atlassian']
#filterno = [120,150,180,210,240,270,300,330,360]
#timeno = [1,1,1,1,1,1,1,1,1,1,1,1]
#timeno = [6,8,9,11,13,14,15,16,17,18,18,20] #moodle q2
#timeno = [16,22,30,36,40,42,46,53,56,61,64,76] #moodle q3
#timeno = [4,5,6,6,7,8,8,9,10,10,11,12] #apache q2
#timeno = [9,12,15,18,21,24,28,31,34,37,40,42] #apache q3
# timeno = [8,9,10,11,14,18,19,24] #atlassian q2
#timeno = [2,2,3,3,3,4,4,4,5,5,5,6] #moodle q1
#timeno = [2,2,2,2,3,3,3,3,3,4,4,4] #apache q1
#timeno = [2,3,3,3,4,5,5,5,5] #atlassian q1

# for d in dataset:
#     i = 0
#     for n in filterno:
#         print('allMatch', 'actual/new/actual_team_'+d+'.json', 'out/output/hitmiss/'+d+'/filter/output_our_hitnohit_'+d+'_'+str(n)+'_'+str(timeno[i])+'.json', 'result/'+d+'/hitmiss/filter/eval_our_'+d+'_'+str(n)+'_'+str(timeno[i])+'.txt')

#         main_eval('allMatch', 'actual/new/actual_team_'+d+'.json', 'out/output/hitmiss/'+d+'/filter/output_our_hitnohit_'+d+'_'+str(n)+'_'+str(timeno[i])+'.json', 'result/'+d+'/hitmiss/filter/eval_our_'+d+'_'+str(n)+'_'+str(timeno[i])+'.txt')
#         i = i+1
