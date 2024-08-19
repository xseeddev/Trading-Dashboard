import React, { Dispatch, SetStateAction } from 'react'
import Form from '../components/Form'
import ActivityLog from '../components/ActivityLog'

const Dashboard = ({setLoggedIn}:{setLoggedIn:Dispatch<SetStateAction<string | null>>}) => {
  return (
    <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-5">Trade Dashboard</h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

            <Form setLoggedIn={setLoggedIn}></Form>
            <ActivityLog></ActivityLog>

        </div>
    </div>
  )
}

export default Dashboard