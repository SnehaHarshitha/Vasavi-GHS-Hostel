 
import {useState} from "react"; 
import "./todolist.css" 
function ToDoListApp(){ 
    let[TodoInput,setInput]=useState("") 
    let[list,setList]=useState([ 
        { 
            "id":1, 
            "task":"ReactJS" 
        }, 
        { 
            "id":2, 
            "task":"NodeJS" 
        }, 
        { 
            "id":3, 
            "task":"HTML" 
        }, 
    ]) 
    let newId=list.length+1 
    function AddTask(){ 
        if(TodoInput=="") 
        { 
            alert("Please provide task") 
        } 
        else 
            { 
            let newTask=[ 
                ...list, 
                { 
                    "id":newId, 
                    "task":TodoInput 
                } 
            ] 
            setList(newTask) 
            setInput("") 
 
        } 
    } 
    function deleteTask(id){ 
    let delList=list.filter((t)=>{ 
        return (t.id!==id) 
    }) 
    setList(delList) 
   } 
 
    return( 
        <div className="container mt-5 w-50"> 
            <h1>ToDoListApp</h1> 
            <div className="input-group"> 
                <input className="form-control" type="text" 
                onChange={(e)=>{ 
                    setInput(e.target.value) 
                }} 
                value={TodoInput}/> 
                <button type="button" className="btn btn-primary"  
                onClick={AddTask}>ADD</button> 
            </div> 
            <ul className="list-group"> 
                { 
                    list.map((t)=>{ 
                        return <li className="list-group-item">{t.task} 
                        <button className="btn" onClick={()=>deleteTask(t.id)}> </button></li> 
                    }) 
                } 
            </ul> 
        </div> 
    ) 
} 
 
export default ToDoListApp;