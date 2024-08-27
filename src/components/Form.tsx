import React, { Dispatch, SetStateAction, useEffect, useState } from 'react'
import { SubmitHandler, useForm } from 'react-hook-form';
import toast from 'react-hot-toast';


type FormValues = {
    trade_operation: string,
    buy_strike: number,
    sell_strike: number,
    option_type: string,
    expiry_pref: number,
    nf_target: number,
    nf_sl: number,
    pnl_target: number,
    pnl_sl: number
  };



const Form = ({setLoggedIn}:{setLoggedIn:Dispatch<SetStateAction<string|null>>}) => {

    const [data, setData] = useState({});
    const { register, handleSubmit, setValue } = useForm<FormValues>();

    useEffect(()=>{
        const fetchData = async () => {
            const response = await fetch('http://127.0.0.1:5000/api/read');
            const data = await response.json();
            setData(data);
        }
        fetchData();
    },[])

    useEffect(() => {
        if (data) {
          Object.keys(data).forEach(key => {
            //@ts-ignore
            setValue(key, data[key]);
          });
        }
      }, [data, setValue]);

    const onSubmit: SubmitHandler<FormValues> = (newData) => {
        const dataToSend = {
            ...newData,
            buy_strike: Number(newData.buy_strike),
            sell_strike: Number(newData.sell_strike),
            expiry_pref: Number(newData.expiry_pref),
            nf_target: Number(newData.nf_target),
            nf_sl: Number(newData.nf_sl),
            pnl_target: Number(newData.pnl_target),
            pnl_sl: Number(newData.pnl_sl),
        };
        toast.loading('Writing data...')
        fetch('http://127.0.0.1:5000/api/checkToken', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `${localStorage.getItem('token')}`
          },
          body: JSON.stringify({data:dataToSend}),
        })
          .then(response => response.json())
          .then(data => {
            toast.dismiss();
            if(data.success){
              toast.success('Data written successfully');
              fetch('http://127.0.0.1:5000/api/read')
                .then(response => response.json())
                .then(data => setData(data));
                return;
            }
            toast.error('Session expired please login again.')
          })
          .catch((error) => {
            setLoggedIn(null)
            localStorage.removeItem('token');
            toast.dismiss();
            toast.error('Error writing data');
            console.error('Error:', error);
          });
        
      };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="flex flex-col">
                <label htmlFor="trade_operation" className="text-sm font-medium text-gray-700 mb-1">Trade Operation</label>
                <select {...register("trade_operation")} className="mt-1 block w-full px-2 py-3 font-semibold outline-none rounded-md border border-gray-300 shadow-sm focus:border-indigo-500 focus:ring focus:ring-indigo-200 focus:ring-opacity-50">
                  <option value="NEW_TRADE">NEW_TRADE</option>
                  <option value="TRADE_EXIT">TRADE_EXIT</option>
                  <option value="AUTO_TRADE_EXIT">AUTO_TRADE_EXIT</option>
                  <option value="-1">-1</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col">
                  <label htmlFor="buy_strike" className="text-sm font-medium text-gray-700 mb-1">Buy Strike</label>
                  <input type="number" id="buy_strike" {...register("buy_strike")} className="mt-1 block w-full rounded-md border px-2 py-3 font-semibold outline-none border-gray-300 shadow-sm focus:border-indigo-500 focus:ring focus:ring-indigo-200 focus:ring-opacity-50" />
                </div>
                <div className="flex flex-col">
                  <label htmlFor="sell_strike" className="text-sm font-medium text-gray-700 mb-1">Sell Strike</label>
                  <input type="number" id="sell_strike" {...register("sell_strike")} className="mt-1 block w-full rounded-md border px-2 py-3 font-semibold outline-none border-gray-300 shadow-sm focus:border-indigo-500 focus:ring focus:ring-indigo-200 focus:ring-opacity-50" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col">
                  <label htmlFor="option_type" className="text-sm font-medium text-gray-700 mb-1">Option Type</label>
                  <select {...register("option_type")} className="mt-1 block w-full rounded-md border border-gray-300 shadow-sm px-2 py-3 font-semibold outline-none focus:border-indigo-500 focus:ring focus:ring-indigo-200 focus:ring-opacity-50">
                    <option value="CE">CE</option>
                    <option value="PE">PE</option>
                    <option value="-1">-1</option>
                  </select>
                </div>

                <div className="flex flex-col">
                  <label htmlFor="expiry_pref" className="text-sm font-medium text-gray-700 mb-1">Expiry Preference</label>
                  <select {...register("expiry_pref")} className="mt-1 block w-full rounded-md border border-gray-300 shadow-sm px-2 py-3 font-semibold outline-none focus:border-indigo-500 focus:ring focus:ring-indigo-200 focus:ring-opacity-50">
                    <option value="0">0</option>
                    <option value="1">1</option>
                    <option value="2">2</option>
                    <option value="3">3</option>
                    <option value="4">4</option>
                    <option value="-1">-1</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col">
                  <label htmlFor="nf_target" className="text-sm font-medium text-gray-700 mb-1">NF Target</label>
                  <input type="number" id="nf_target" {...register("nf_target")} className="mt-1 block w-full rounded-md border border-gray-300 shadow-sm focus:border-indigo-500 px-2 py-3 font-semibold outline-none focus:ring focus:ring-indigo-200 focus:ring-opacity-50" />
                </div>
                <div className="flex flex-col">
                  <label htmlFor="nf_sl" className="text-sm font-medium text-gray-700 mb-1">NF SL</label>
                  <input type="number" id="nf_sl" {...register("nf_sl")} className="mt-1 block w-full rounded-md border border-gray-300 shadow-sm focus:border-indigo-500 px-2 py-3 font-semibold outline-none focus:ring focus:ring-indigo-200 focus:ring-opacity-50" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col">
                  <label htmlFor="pnl_target" className="text-sm font-medium text-gray-700 mb-1">PnL Target</label>
                  <input type="number" id="pnl_target" {...register("pnl_target")} className="mt-1 block w-full rounded-md border border-gray-300 shadow-sm px-2 py-3 font-semibold outline-none focus:border-indigo-500 focus:ring focus:ring-indigo-200 focus:ring-opacity-50" />
                </div>
                <div className="flex flex-col">
                  <label htmlFor="pnl_sl" className="text-sm font-medium text-gray-700 mb-1">PnL SL</label>
                  <input type="number" id="pnl_sl" {...register("pnl_sl")} className="mt-1 block w-full rounded-md border border-gray-300 shadow-sm focus:border-indigo-500 px-2 py-3 font-semibold outline-none focus:ring focus:ring-indigo-200 focus:ring-opacity-50" />
                </div>
              </div>

              <button type="submit" className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                Submit
              </button>
            </form>
          </div>
  )
}

export default Form