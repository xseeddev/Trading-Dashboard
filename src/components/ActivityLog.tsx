import React, { useEffect, useState } from 'react'

const ActivityLog = () => {
const [log, setLog] = useState<any>({});

  useEffect(() => {
    const fetchData = async()=>{
      const logResponse = await fetch('http://localhost:5000/api/log');
      const logData = await logResponse.json();
      setLog(logData);
    };
    const intervalId = setInterval(fetchData, 2000); 

    return () => {
     clearInterval(intervalId); 
   };
  }, []);

  const today = new Date();
  const formattedDate = `${today.getFullYear()}-${String(today.getDate()).padStart(2, '0')}-${String(today.getMonth() + 1).padStart(2, '0')}`;


  return (
    <div className="bg-white rounded-lg shadow-md p-6 ">
        <h2 className="text-2xl font-semibold text-gray-700 mb-3">Activity Log</h2>
        <div className="space-y-2 scroll-auto">
          <h3 className="text-lg font-medium text-gray-800 mb-2">{formattedDate}</h3>
          <ul className="list-disc overflow-y-auto max-h-[400px] scroll-auto list-inside space-y-1">
            {
              log[formattedDate] && log[formattedDate].map((message:string, index:number) => (
                <li key={index} className="text-sm text-gray-800">{message}</li>
              ))
            }
          </ul>
        </div>
    </div>
  )
}

export default ActivityLog