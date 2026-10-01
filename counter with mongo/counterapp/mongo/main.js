const express=require("express") 
const mongoose=require("mongoose") 
const app=express() 
const PORT=7000 
app.use(express.json()); 
mongoose.connect("mongodb://localhost:27017/vasavi") 
.then(()=>{ 
console.log("MongoDb connnected successfully") 
}) 
.catch(()=>{ 
    console.log("Mongodb Not Connected") 
}) 
const stdSchema = new mongoose.Schema( 
    { 
        _id: Number, 
        sname: String, 
        sno: Number 
    }, 
    { versionKey: false } 
); 
 
const std = mongoose.model("students", stdSchema); 
  
 
app.get("/",(req,res)=>{ 
    res.send("<h1>welcome to MongoDb Application</h1>") 
}) 
app.get("/allstds",async (req,res)=> 
{ 
    const stds=await std.find({}) 
    res.send(stds) 
}) 
 
 
app.post("/newStd", async (req, res) => { 
     console.log("Incoming body:", req.body);  
    try { 
        const newStd = new std({ 
            _id: req.body._id, 
            sname: req.body.sname, 
             sno: Number(req.body.sno)  
        }); 
 
        const stdSave = await newStd.save(); 
        console.log("New Record Inserted Successfully"); 
        res.status(201).send(stdSave); 
    } catch (err) { 
        console.error("Error inserting record:", err); 
        res.status(400).send("Error inserting record: " + err.message); 
    } 
}); 
 
app.put("/update/:id",async(req,res)=>{ 
    const id=parseInt(req.params.id) 
    const updateData=req.body 
    const updateStd=await std.findByIdAndUpdate(id,updateData,{new:true}); 
    if(!updateStd) 
    { 
        res.send("Student is not found in DB") 
    } 
    else 
    { 
        res.send(updateStd); 
    } 
}); 
app.delete("/delete/:id",async(req,res)=>{ 
    const id=parseInt(req.params.id) 
    const deleteStd=await std.findByIdAndDelete(id); 
    if(!deleteStd) 
    { 
        res.send("Student not in DB") 
    } 
    else 
    { 
        res.send("Student Deleted Successfully") 
    } 
}); 
 app.listen(PORT,()=>{ 
    console.log("Server running at",PORT) 
})