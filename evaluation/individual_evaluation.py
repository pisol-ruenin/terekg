from evaluation_final import evaluation
from evaluation_final import getEvaluationValue
import evaluation_final as eva
import os
import pandas as pd
import json
import xlsxwriter

# moodle = ['dev','integrator','peer','tester']
# apache = ['dev','peer']
# atlassian = ['dev', 'peer', 'tester']
roleFullName = {'dev':'developer','integrator':'integrator','peer':'reviewer','tester':'tester'}

def getRoleParameter(datasetName):
    if datasetName == 'moodle':
        return ['dev']#,'integrator','peer','tester']
    elif datasetName =='apache':
        return ['dev','peer']
    elif datasetName == 'atlassian':
        return  ['dev','peer', 'tester']
    else:
        return []


def allRoleEvaluation(dataset, path, role, outfile):
    actual = []
    result = []
    with open('actual/new/actual_team_'+dataset+'.json') as json_file:
        data2 = json.load(json_file)
        actual = pd.DataFrame(data2)
        actual.set_index('issue',inplace=True)
    
    delayissue = pd.read_csv('delayissue/delayissue_'+dataset+'.csv')
    delayissue = set(delayissue['issuekey'])
    
    allMatch = [] #Store list of comparing result of every issue
    precision = []
    bprefResult = []   
    maprecision = []   
    avgMatchTeam = 0
    countMatch = 0
    matchTeamSize = []
    
    print(path)    
    for ro in role:
        fileName = path+ro+'.json'
        with open(fileName) as json_file:
            data = json.load(json_file)
            result = pd.DataFrame(data)
        
        print(ro, len(result))
        # result = result[:10]
        for i, r in result.iterrows():
            if r['issue'] not in delayissue:
                actualTeam = actual.loc[r['issue']]['r'][0]['team']
                teamSize = len(actualTeam['developer'])+len(actualTeam['integrator'])+len(actualTeam['reviewer'])+len(actualTeam['tester']) 
                checkMatch = eva.checkIndividual(roleFullName[ro],actualTeam, r['r'])
                
                if checkMatch.count(1) != 0:
                    # print(r['issue']+'  '+str(r['r'][checkMatch.index(1)]))
                    avgMatchTeam = avgMatchTeam + teamSize+1
                    countMatch = countMatch +1
                    matchTeamSize.append(teamSize+1)
    
                allMatch.append(checkMatch)
                p = eva.pak(checkMatch)
                precision.append(p)
                maprecision.append(eva.MAP(checkMatch, p))
            
    # file = open(outfile,"a") 
    precisioncol = [ 'P @ '+str(i+1) for i in range(10)]
            
    mrrval = eva.mrr(allMatch)
    hit_temp = eva.hitAt10(allMatch)
    hit = sum(hit_temp)/len(hit_temp)
    hit100_temp = eva.hitAt100(allMatch)
    hit100 = sum(hit100_temp)/len(hit100_temp)
    MR = eva.meanRank(allMatch)
    MRall= eva.meanRankAll(allMatch)
    avgTeamSize = avgMatchTeam/countMatch
    MAPval = sum(maprecision)/len(maprecision)
    precisionList = eva.averagePrecision(precision)

    print('---------------------------individual Match---------------------------')
    print('MRR: ', mrrval)
    print('hit at 10: ', hit)
    print('hit at 100: ', hit100)
    print('MR: ', MR)
    print('MR of all recommendation: ', MRall)
    print('Size of Match team: ', avgTeamSize)
    print('Number of Match team: ', countMatch)
    print('MAP: ', MAPval)
    print('average precision at K: ', precisionList[:10])
            
    # file.write('---------------------------individual Match---------------------------\n')
    # file.write('MRR: '+str(mrrval)+ '\n')
    # file.write('MR: '+str(MR)+ '\n')
    # file.write('MR of all recommendation: '+str(MRall)+'\n')
    # file.write('hit at 10: '+ str(hit)+'\n')
    # file.write('hit at 100: '+ str(hit100)+'\n')
    # file.write('MAP: '+ str(MAPval)+'\n')
    # file.write('avgTeamSize: '+ str(avgTeamSize)+'\n')
    # file.write('average precision at K: '+str(precisionList)+'\n')
    
    excel = outfile.replace('.txt', '.xlsx')
    workbook = xlsxwriter.Workbook(excel) 
    worksheet = workbook.add_worksheet('individual') 
    resultrow = [ 
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
        resultrow.append([precisioncol[i], precisionList[i]])
        # Start from the first cell. Rows and 
        # columns are zero indexed. 
            
    resulttuple = tuple(resultrow)
    row = 0
    col = 0

    #Iterate over the data and write it out row by row. 
    for name, score in (resulttuple): 
        worksheet.write(row, col, name) 
        worksheet.write(row, col + 1, score) 
        row += 1
    workbook.close()        
    img = outfile.replace('.txt', '_individual.png')
    eva.saveTeamSizeDistribution(matchTeamSize, img)
        
    data = pd.DataFrame({'precision': precision,'maprecision': maprecision,'hit': hit_temp, 'hit100': hit100_temp})
    pklfile = outfile.replace('.txt', '_individual_info'+'.pkl')
    data.to_pickle(pklfile)
    
def singleRoleEvaluation(dataset, path, role, outfile, workbook):
    actual = []
    result = []
    with open('actual_team_'+dataset+'.json') as json_file:
        data2 = json.load(json_file)
        actual = pd.DataFrame(data2)
        actual.set_index('issue',inplace=True)
        
    # delayissue = pd.read_csv('delayissue/delayissue_'+dataset+'.csv')
    # delayissue = set(delayissue['issuekey'])
        
    allMatch = [] #Store list of comparing result of every issue
    precision = []
    bprefResult = []   
    maprecision = []   
    avgMatchTeam = 0
    countMatch = 0
    matchTeamSize = []
       
    if 1 == 1:
        fileName = path+role+'.json'
        with open(fileName) as json_file:
            data = json.load(json_file)
            result = pd.DataFrame(data)
        
        print(role, len(result))
        # result = result[:10]
        for i, r in result.iterrows():
            if 1 ==1:
                actualTeam = actual.loc[r['issue']]['r'][0]['team']
                teamSize = len(actualTeam['developer'])+len(actualTeam['integrator'])+len(actualTeam['reviewer'])+len(actualTeam['tester']) 
                checkMatch = eva.checkIndividual(roleFullName[role],actualTeam, r['r'])
                
                if checkMatch.count(1) != 0:
                    # print(r['issue']+'  '+str(r['r'][checkMatch.index(1)]))
                    avgMatchTeam = avgMatchTeam + teamSize+1
                    countMatch = countMatch +1
                    matchTeamSize.append(teamSize+1)
    
                allMatch.append(checkMatch)
                p = eva.pak(checkMatch)
                precision.append(p)
                maprecision.append(eva.MAP(checkMatch, p))
            
    # file = open(outfile,"a") 
    precisioncol = [ 'P @ '+str(i+1) for i in range(10)]
            
    mrrval = eva.mrr(allMatch)
    hit_temp = eva.hitAt10(allMatch)
    hit = sum(hit_temp)/len(hit_temp)
    hit100_temp = eva.hitAt100(allMatch)
    hit100 = sum(hit100_temp)/len(hit100_temp)
    MR = eva.meanRank(allMatch)
    MRall= eva.meanRankAll(allMatch)
    avgTeamSize = avgMatchTeam/countMatch
    MAPval = sum(maprecision)/len(maprecision)
    precisionList = eva.averagePrecision(precision)

    print('---------------------------individual Match---------------------------')
    print('MRR: ', mrrval)
    print('hit at 10: ', hit)
    print('hit at 100: ', hit100)
    print('MR: ', MR)
    print('MR of all recommendation: ', MRall)
    print('Size of Match team: ', avgTeamSize)
    print('Number of Match team: ', countMatch)
    print('MAP: ', MAPval)
    print('average precision at K: ', precisionList[:10])
            
    # file.write('---------------------------individual Match---------------------------\n')
    # file.write('MRR: '+str(mrrval)+ '\n')
    # file.write('MR: '+str(MR)+ '\n')
    # file.write('MR of all recommendation: '+str(MRall)+'\n')
    # file.write('hit at 10: '+ str(hit)+'\n')
    # file.write('hit at 100: '+ str(hit100)+'\n')
    # file.write('MAP: '+ str(MAPval)+'\n')
    # file.write('avgTeamSize: '+ str(avgTeamSize)+'\n')
    # file.write('average precision at K: '+str(precisionList)+'\n')
    
    worksheet = workbook.add_worksheet(role) 
    resultrow = [ 
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
        resultrow.append([precisioncol[i], precisionList[i]])
        # Start from the first cell. Rows and 
        # columns are zero indexed. 
            
    resulttuple = tuple(resultrow)
    row = 0
    col = 0

    #Iterate over the data and write it out row by row. 
    for name, score in (resulttuple): 
        worksheet.write(row, col, name) 
        worksheet.write(row, col + 1, score) 
        row += 1    
    # img = outfile.replace('.txt', '_individual.png')
    # eva.saveTeamSizeDistribution(matchTeamSize, img)
        
    # data = pd.DataFrame({'precision': precision,'maprecision': maprecision,'hit': hit_temp, 'hit100': hit100_temp})
    # pklfile = outfile.replace('.txt', '_individual_info'+'.pkl')
    # data.to_pickle(pklfile)


def allApproachEvaluation(datasetName, outpath):
    role = getRoleParameter(datasetName)
    approach = ['random','haibin','dump','our']
    path = ''
    for i in approach:
        if i == 'our':
            path = 'out/output/individualrec/'+i+'/output_'+i+'_hitnohit_'+datasetName+'_'
        elif i == 'random' or i == 'dump':
            path = 'out/output/individualrec/'+i+'/output_'+i+'_'+datasetName+'_'
        elif i == 'haibin':
            path = 'out/output/individualrec/'+i+'/output_nonneghaibin_'+datasetName+'_'
        outfile = outpath+datasetName+'/'+i+'/'+'eval_individual_'+i+'_'+datasetName+'.txt'
        allRoleEvaluation(datasetName, path, role, outfile)
    
# allApproachEvaluation('moodle', 'result/individualrec/nodelay/')
# allApproachEvaluation('apache', 'result/individualrec/nodelay/')
# allApproachEvaluation('atlassian', 'result/individualrec/nodelay/')
        
def allApproachSingleRoleEvaluation(datasetName, outpath):
    role = getRoleParameter(datasetName)
    approach = ['our']
    path = ''
    for i in approach:
        if i == 'our':
            path = 'individual_search_result_'
        elif i == 'random' or i == 'dump':
            path = 'out/output/individualrec/'+i+'/new/output_'+i+'_'+datasetName+'_'
        elif i == 'haibin':
            path = 'out/output/individualrec/'+i+'/new/output_nonneghaibin_'+datasetName+'_'
        outfile = outpath+'eval_individual_singleRole_'+i+'_'+datasetName+'.txt'
        
        
        excel = outfile.replace('.txt', '.xlsx')
        workbook = xlsxwriter.Workbook(excel) 
        for r in role:
            singleRoleEvaluation(datasetName, path, r, outfile, workbook)
        workbook.close()    

allApproachSingleRoleEvaluation('moodle', './')
# allApproachSingleRoleEvaluation('apache', 'result/individualrec/')
#allApproachSingleRoleEvaluation('atlassian', 'result/individualrec/')
