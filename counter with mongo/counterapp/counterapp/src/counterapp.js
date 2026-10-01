import "./counterapp.css" 
import React,{useState} from "react"; 
function CounterApp(){ 
    let[count,setCount] = useState(0) 
    let stock = 10; 
    return( 
        <> 
        <h1 align='center'> Item </h1> 
        <div className="container"> 
            <button className="minus" disabled={count==0}  
            onClick={()=>{ 
                if(count >0) 
                { 
                    setCount(--count) 
                } 
            }}>-</button> 
            <p>{count}</p> 
            <button className="plus" disabled={stock==count} 
            onClick={()=>{ 
                if(stock) 
                { 
                    setCount(++count) 
                } 
            }}>+</button> 
        </div> 
        </> 
    ) 
} 
export default CounterApp;