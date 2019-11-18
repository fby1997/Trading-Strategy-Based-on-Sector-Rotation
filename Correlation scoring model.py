import pandas as pd
import numpy as np
import math
from functools import reduce
from scipy.stats.stats import pearsonr
from matplotlib import pyplot as plt

data_path=r'./SWI closing price.xlsx'
#columns_list=['801040.SWI','801180.SWI','801710.SWI']
data=pd.read_excel(data_path)
columns_list=list(data.head(0))[1:]
data_question1=data[columns_list]

for industry in list(data_question1.head(0)):
    data_question1[industry+'_Lag1'] = data_question1[industry].shift(periods=-1,axis=0)
    data_question1[industry+'_rate'] = data_question1[industry]/data_question1[industry+'_Lag1']
    data_question1[industry+'_lograte'] = np.log(data_question1[industry+'_rate'])
data_question1.dropna(inplace=True)
data_question1_rate=data_question1[[x+'_rate' for x in columns_list]]

out=[]
columns_list_rate=[x+'_lograte' for x in list(data.head(0))[1:]]

for pair_one in columns_list_rate:
    for pair_two in columns_list_rate:
        pair_one_l = list(data_question1[pair_one])
        pair_two_l = list(data_question1[pair_two])
        
        start_one = 0
        for i in range(10):
            
            start_two =0 
            for j in range(10):
                
                if start_one < start_two:
                    sli_one = pair_one_l[start_one: start_one+300]
                    sli_two=pair_two_l[start_two: start_two+300]
                    corr = pearsonr(sli_one,sli_two)[0]
                    if corr >0.1 and corr <1.0:
                        out.append([pair_one,pair_two,start_one,start_two,corr])
                    
                start_two+=30
                
            start_one+=30
            
autocorr = [item for item in out if item[0]==item[1]]
cross =  [item for item in out if item[0]!=item[1]]

data_score = pd.DataFrame()
data_score[columns_list] = data_question1[[x+'_lograte' for x in columns_list]]
for field in columns_list:
    data_score[field+'_score'] = 0
data_score.dropna(inplace=True)

for i in range(len(cross)):
    field1 = cross[i][0][:-8]
    field2 = cross[i][1][:-8]
    lag1 = cross[i][2]
    lag2 = cross[i][3]
    coef = cross[i][4]
    for t in range(1,301):
        if data_score.loc[t+lag1,field1] > 0:
            data_score.loc[t+lag2,field2+'_score'] += coef
        elif data_score.loc[t+lag1,field1] < 0:
            data_score.loc[t+lag2,field2+'_score'] -= coef
            
score_list=[x+'_score' for x in columns_list]
data_score_n=data_score[score_list]

def Score_rank(t,score_list,data_score_n,data_score):
    total=1
    for i in range(len(score_list)):
        total+=math.exp(np.array(data_score_n[score_list])[t][i])
    
    weight = [math.exp(np.array(data_score_n[score_list])[t][i])/total for i in range(len(score_list))]
    weight = weight+[1/total]
    value_rate = np.dot(np.array(data_question1_rate)[t],np.array(weight)[:-1])+np.array(weight)[-1]
    return weight,value_rate

value_total=[1]
weight_total=[[0]*27+[1]]
for t in range(len(np.array(data_score))):
    weight_total.append(Score_rank(t,score_list,data_score_n,data_score)[0])
    value_total.append(Score_rank(t,score_list,data_score_n,data_score)[1])

value_day=[1]
for i in range(1,len(value_total)):
    value_day.append(reduce(lambda x,y:x*y, value_total[:i]))
plt.plot(value_day[:500])

Annual_rate=(value_day[500])**(250/500)-1
def max_withdrawal(data):
    mw=((pd.DataFrame(data).cummax()-pd.DataFrame(data))/pd.DataFrame(data).cummax()).max()
    return round(mw,4)
Maximum_withdrawal=max_withdrawal(value_day[:500])

from scipy import stats
data_index=pd.read_excel(r'./baseline.xlsx')
data_index=list(data_index['close'])[:500]
Beta,Alpha,R_value,P_value,Std_err=stats.linregress(data_index,value_day[:500])
print(Annual_rate,Maximum_withdrawal,Beta,Alpha,R_value,P_value,Std_err)