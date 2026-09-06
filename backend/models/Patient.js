const mongoose=require('mongoose');
const schema=new mongoose.Schema({
  patientId:{type:String,required:true,trim:true},
  owner:{type:mongoose.Schema.Types.ObjectId,ref:'User',required:true},
  name:{type:String,required:true,trim:true},
  condition:{type:String,enum:['cardiovascular','diabetes'],default:'cardiovascular',index:true},
  age:{type:Number,required:true,min:0,max:120},
  gender:{type:Number,min:1,max:2},height:{type:Number,min:80,max:250},weight:{type:Number,min:20,max:300},ap_hi:{type:Number,min:60,max:300},ap_lo:{type:Number,min:30,max:200},cholesterol:{type:Number,min:1,max:3},gluc:{type:Number,min:1,max:3},smoke:{type:Number,min:0,max:1},alco:{type:Number,min:0,max:1},active:{type:Number,min:0,max:1},bmi:{type:Number,min:10,max:80},
  diabetesGender:{type:String,trim:true},hypertension:{type:Number,min:0,max:1},heart_disease:{type:Number,min:0,max:1},smoking_history:{type:String,trim:true},HbA1c_level:{type:Number,min:3,max:20},blood_glucose_level:{type:Number,min:40,max:500}
},{timestamps:true});
schema.index({owner:1,patientId:1},{unique:true});
module.exports=mongoose.model('Patient',schema);
