"""SIMULATED chapter 44 experiment. Refuse to overwrite prior runs."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from quant_course.stochastic_calculus import brownian_increments, quadratic_variation, ito_left, gbm_exact, gbm_euler
from quant_course.derivatives_pricing import bs_price, bs_greeks, crr_price, mc_price, delta_hedge

PARAMS = dict(S=100., K=100., T=1., r=.05, q=.02, sigma=.2)


def finite_difference_greeks(params: dict, kind: str, h: float = 1e-4) -> dict:
    """Centered derivatives; theta is calendar time, vega per unit sigma."""
    if not np.isfinite(h) or h <= 0 or h >= min(1., params["T"], params["sigma"]):
        raise ValueError("h must be positive, finite, and keep centered parameters in range")
    def v(key=None, shift=0.):
        a = params.copy()
        if key is not None:
            a[key] += shift
        return bs_price(**a, kind=kind)
    hs = h * params["S"]
    return {"delta": (v("S", hs)-v("S", -hs))/(2*hs),
            "gamma": (v("S", hs)-2*v()+v("S", -hs))/hs**2,
            "vega": (v("sigma", h)-v("sigma", -h))/(2*h),
            "theta": -(v("T", h)-v("T", -h))/(2*h),
            "rho": (v("r", h)-v("r", -h))/(2*h)}


def _json(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(type(value).__name__)


def run_experiment(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    figdir = output / "figures"
    figdir.mkdir()
    def figure(name, xlabel, ylabel):
        plt.xlabel(xlabel); plt.ylabel(ylabel)
        plt.title("SIMULATED / CONSTRUCTED")
        plt.tight_layout(); plt.savefig(figdir/name, dpi=150); plt.close()
    res = {"classification": "SIMULATED / CONSTRUCTED", "params": PARAMS,
           "protocol": "qa/a9/ch44_batch/INTERFACE_AND_PROTOCOL.md", "confidence": .95}
    res["bs"] = {k: bs_price(**PARAMS, kind=k) for k in ["call", "put"]}
    res["parity_residual"] = res["bs"]["call"]-res["bs"]["put"]-100*np.exp(-.02)+100*np.exp(-.05)
    # Hand tree: stock 120/80, strike 100, bank grows by 1.05.
    delta=.5; cash=-40/1.05; tree_value=delta*100+cash
    res["one_step"] = dict(delta=delta,cash=cash,value=tree_value,p=(1.05-.8)/(.4),up=delta*120+cash*1.05,down=delta*80+cash*1.05)
    res["trees"] = []
    for n in [10,25,50,51,100,101,200,400]:
        row={"steps":n}
        for k in ["call","put"]:
            row[k]=crr_price(**PARAMS,kind=k,steps=n)
            row[k+"_error"]=row[k]-res["bs"][k]
        res["trees"].append(row)
    plt.figure(); plt.axhline(0,color="gray")
    plt.plot([x["steps"] for x in res["trees"]],[x["call_error"] for x in res["trees"]],"o-",label="call")
    plt.plot([x["steps"] for x in res["trees"]],[x["put_error"] for x in res["trees"]],"s-",label="put"); plt.legend()
    figure("fig44_tree.png","CRR steps","Tree minus BS (currency/share)")
    res["mc"]=[]
    for pairs in [1000,5000,25000,50000]:
        for k in ["call","put"]:
            row=mc_price(**PARAMS,kind=k,pairs=pairs,seed=4401,antithetic=True)
            res["mc"].append(dict(kind=k,pairs=pairs,**row))
    z=np.random.default_rng(4401).standard_normal(50000)
    st=100*np.exp((.05-.02-.5*.2**2)+.2*z); stanti=100*np.exp((.05-.02-.5*.2**2)-.2*z)
    np.savez(output/"mc_raw.npz",z=z,st=st,stanti=stanti)
    res["mc_plain"]=mc_price(**PARAMS,kind="call",pairs=50000,seed=4401,antithetic=False)
    plt.figure()
    rows=[x for x in res["mc"] if x["kind"]=="call"]
    plt.errorbar([x["pairs"] for x in rows],[x["price"] for x in rows],yerr=[1.95996398454*x["se"] for x in rows],fmt="o")
    plt.axhline(res["bs"]["call"],color="gray",label="BS"); plt.xscale("log"); plt.legend()
    figure("fig44_mc.png","Independent pairs (log scale)","Call price and 95% normal CI")
    dw=brownian_increments(1024,1024,1.,4402)
    W=np.column_stack([np.zeros(1024),np.cumsum(dw,axis=1)])
    np.savez(output/"brownian_raw.npz",increments=dw)
    res["brownian"]=[]
    plt.figure(figsize=(8,4))
    for row in W[:4]: plt.plot(np.linspace(0,1,1025),row,lw=.8)
    figure("fig44_brownian.png","Time (years)","W (sqrt(years))")
    for n in [16,64,256,1024]:
        d=dw.reshape(1024,n,1024//n).sum(axis=2); w=np.column_stack([np.zeros(1024),np.cumsum(d,axis=1)])
        qv=quadratic_variation(w); integ=ito_left(w,w[:,:-1]); exact_finite=.5*(w[:,-1]**2-qv); limit=.5*(w[:,-1]**2-1)
        assert np.max(np.abs(integ-exact_finite)) < 1e-12
        res["brownian"].append(dict(steps=n,qv_mean=float(qv.mean()),qv_sd=float(qv.std(ddof=1)),finite_residual=float(np.max(np.abs(integ-exact_finite))),limit_rmse=float(np.sqrt(np.mean((integ-limit)**2)))))
    plt.figure(); plt.plot([x["steps"] for x in res["brownian"]],[x["qv_mean"] for x in res["brownian"]],"o-"); plt.axhline(1,color="gray"); plt.xscale("log")
    figure("fig44_qv.png","Steps (log scale)","Mean quadratic variation (years)")
    # The integral prefix depends only on the prefix of both paths and integrands.
    w2=W.copy(); w2[:,513:]+=3
    assert np.array_equal(ito_left(W[:,:513],W[:,:512]),ito_left(w2[:,:513],w2[:,:512]))
    res["adapted_prefix_check"]=True
    gdw=brownian_increments(4096,1024,1.,4403)
    np.savez(output/"gbm_raw.npz",increments=gdw)
    res["gbm"]=[]
    for n in [16,64,256,1024]:
        d=gdw.reshape(4096,n,1024//n).sum(axis=2)
        exact=gbm_exact(100,.06,.2,1/n,d); euler=gbm_euler(100,.06,.2,1/n,d)
        err=euler[:,-1]-exact[:,-1]
        res["gbm"].append(dict(steps=n,strong_rmse=float(np.sqrt(np.mean(err**2))),weak_paired_mean=float(err.mean()),weak_paired_se=float(err.std(ddof=1)/np.sqrt(len(err))),negative_values=int(np.sum(euler<0))))
    plt.figure(); plt.hist(exact[:,-1],bins=50,alpha=.7)
    figure("fig44_gbm.png","P terminal ex-dividend S (currency/share)","Paths (4096)")
    plt.figure(); plt.loglog([x["steps"] for x in res["gbm"]],[x["strong_rmse"] for x in res["gbm"]],"o-")
    figure("fig44_euler.png","Steps","Terminal strong RMSE (currency/share)")
    res["greeks"]=[]
    for s in [80.,100.,120.]:
        for k in ["call","put"]:
            a=dict(PARAMS,S=s); analytic=bs_greeks(**a,kind=k); fd=finite_difference_greeks(a,k)
            res["greeks"].append(dict(S=s,kind=k,analytic=analytic,fd=fd,max_error=max(abs(analytic[x]-fd[x]) for x in fd)))
    sgrid=np.linspace(50,150,101); plt.figure()
    for k in ["call","put"]: plt.plot(sgrid,[bs_greeks(**dict(PARAMS,S=s),kind=k)["delta"] for s in sgrid],label=k)
    plt.legend(); figure("fig44_delta.png","Spot S (currency/share)","Delta (shares per option)")
    res["fd_step_sensitivity"]=[]
    for h in [1e-2,1e-4,1e-6,1e-8]:
        fd=finite_difference_greeks(PARAMS,"call",h); ana=bs_greeks(**PARAMS,kind="call")
        res["fd_step_sensitivity"].append(dict(h=h,gamma=fd["gamma"],gamma_error=fd["gamma"]-ana["gamma"]))
    hdw=brownian_increments(256,3276,1.,4404)
    np.savez(output/"hedge_raw.npz",increments=hdw)
    res["hedge"]=[]; hedge_errors={}
    for n in [12,52,252]:
        d=hdw.reshape(256,n,3276//n).sum(axis=2); paths=gbm_exact(100,.06,.2,1/n,d)
        for cost in [0.,.001]:
            outputs=[delta_hedge(path,1.,.05,.02,.2,100.,kind="call",cost_rate=cost) for path in paths]
            errors=np.array([v["error"] for v in outputs]); costs=np.array([v["total_cost"] for v in outputs]); hedge_errors[f"n{n}_cost{cost}"]=errors
            res["hedge"].append(dict(steps=n,cost_rate=cost,mean=float(errors.mean()),sd=float(errors.std(ddof=1)),p05=float(np.quantile(errors,.05)),p95=float(np.quantile(errors,.95)),mean_cost=float(costs.mean())))
            if n==12:
                (output/f"ledger_n12_cost{cost}.json").write_text(json.dumps(outputs[0],default=_json,indent=2))
    np.savez(output/"hedge_errors.npz",**hedge_errors)
    plt.figure()
    for key in ["n12_cost0.0","n252_cost0.0","n252_cost0.001"]: plt.hist(hedge_errors[key],bins=35,alpha=.45,label=key)
    plt.legend(); figure("fig44_hedge.png","Portfolio minus payoff (currency/share)","P paths (256)")
    (output/"results.json").write_text(json.dumps(res,default=_json,ensure_ascii=False,indent=2))
    return res


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",type=Path,required=True)
    args=parser.parse_args()
    results=run_experiment(args.output_dir)
    print(json.dumps({"bs":results["bs"],"output":str(args.output_dir)},ensure_ascii=False))
