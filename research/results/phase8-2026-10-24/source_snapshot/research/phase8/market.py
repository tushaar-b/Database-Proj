"""Point-in-time market matrices, current-weight risk and corporate-action bars."""
import numpy as np
import pandas as pd
from research.risk_metrics import tail_metrics
from research.phase8.policies.construction import hhi


class Market:
    def __init__(self,data):
        self.data=data;self.dates=pd.DatetimeIndex(sorted(data.date.unique()))
        self.tickers=sorted(data.ticker.unique());self.index={t:i for i,t in enumerate(self.tickers)}
        self.sectors=sorted(data.sector.unique());self.sector_index={s:i for i,s in enumerate(self.sectors)}
        labels=data[['ticker','sector']].drop_duplicates().set_index('ticker').sector
        self.sector_matrix=np.zeros((len(self.sectors),len(self.tickers)))
        for ticker in self.tickers:self.sector_matrix[self.sector_index[labels[ticker]],self.index[ticker]]=1
        def matrix(col):return data.pivot(index='date',columns='ticker',values=col).reindex(index=self.dates,columns=self.tickers).to_numpy(float)
        self.prices=matrix('nominal_close');self.splits=matrix('split');self.dividends=matrix('nominal_dividend')
        adjusted=matrix('adjusted_close');self.returns=np.full_like(adjusted,np.nan);self.returns[1:]=adjusted[1:]/adjusted[:-1]-1
        assert np.isfinite(self.prices).all() and (self.prices>0).all()
        self.cov30=np.zeros((len(self.dates),len(self.tickers),len(self.tickers)))
        for i in range(30,len(self.dates)):self.cov30[i]=np.cov(self.returns[i-29:i+1],rowvar=False,ddof=1)

    def state(self,q,cash,di):
        values=q*self.prices[di];stock=float(values.sum());equity=cash+stock
        sector_values=self.sector_matrix@values
        weights={s:float(v/stock) for s,v in zip(self.sectors,sector_values) if v>0} if stock else {}
        result={'stock_value':stock,'equity':equity,'hhi':hhi(values,self.sector_matrix),'weights':weights,
                'max_position_weight':float(values.max()/stock) if stock else np.nan,
                'daily_volatility':np.nan,'parametric_var95':np.nan,'estimated_var95':np.nan,'estimated_cvar95':np.nan}
        if stock:
            window=self.returns[max(1,di-251):di+1];r=window@(values/equity)
            if len(r)>=30:
                result['daily_volatility']=float(np.std(r[-30:],ddof=1));result['parametric_var95']=1.645*result['daily_volatility']
            if len(r)==252:
                tails=tail_metrics(r);result['estimated_var95']=tails['var95'];result['estimated_cvar95']=tails['cvar95']
        result['flags']=(bool(result['parametric_var95']>.10),bool(result['daily_volatility']>.03),bool(result['hhi']>.25))
        return result
