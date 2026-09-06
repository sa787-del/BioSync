require('dotenv').config();
const express=require('express');const mongoose=require('mongoose');const session=require('express-session');const MongoStore=require('connect-mongo');const cors=require('cors');const helmet=require('helmet');const rateLimit=require('express-rate-limit');
const auth=require('./routes/auth');const patients=require('./routes/patients');const dashboard=require('./routes/dashboard');const {requireRole}=require('./middleware/auth');
const app=express();
const isProd=process.env.NODE_ENV==='production';
if(isProd&&(!process.env.SESSION_SECRET||process.env.SESSION_SECRET==='dev-secret'||process.env.SESSION_SECRET.length<32)){throw new Error('SESSION_SECRET must be set to a strong value (32+ characters) in production');}
if(isProd)app.set('trust proxy',1);
app.disable('x-powered-by');app.use(helmet());app.use(cors({origin:process.env.FRONTEND_ORIGIN||'http://localhost:3000',credentials:true}));app.use(express.json({limit:'64kb'}));
const authLimiter=rateLimit({windowMs:15*60*1000,max:100,standardHeaders:true,legacyHeaders:false});
const predictLimiter=rateLimit({windowMs:15*60*1000,max:30,standardHeaders:true,legacyHeaders:false,message:{message:'Too many assessments from this account. Please wait before running another assessment.'}});
app.use('/api/auth/login',authLimiter);app.use('/api/auth/signup',authLimiter);app.use('/api/patients/:id/predict',predictLimiter);
const sessionStore=MongoStore.create({mongoUrl:process.env.MONGO_URI||'mongodb://127.0.0.1:27017/biosync',touchAfter:24*3600});
sessionStore.on('error',(err)=>console.error('Session store error:',err));
app.use(session({secret:process.env.SESSION_SECRET||'dev-secret',resave:false,saveUninitialized:false,store:sessionStore,cookie:{httpOnly:true,sameSite:'lax',secure:isProd,maxAge:86400000}}));
app.get('/health',(req,res)=>res.json({ok:true,service:'biosync-backend'}));app.get('/api/ml-info',requireRole('doctor'),async(req,res)=>{try{const r=await fetch(`${process.env.ML_API_URL||'http://127.0.0.1:8000'}/models`);if(!r.ok)throw new Error('ML service unavailable');res.status(200).json(await r.json())}catch(e){res.status(503).json({message:'Model information unavailable'})}});app.use('/api/auth',auth);app.use('/api/patients',patients);app.use('/api/dashboard',dashboard);
app.use((err,req,res,next)=>{console.error(err);if(res.headersSent)return next(err);if(err.name==='ValidationError'){const details=Object.values(err.errors||{}).map((x)=>x.message).filter(Boolean);return res.status(400).json({message:details.length?`Invalid patient data: ${details.join(' | ')}`:'Invalid patient data'});}res.status(500).json({message:'Server error'});});
mongoose.connect(process.env.MONGO_URI||'mongodb://127.0.0.1:27017/biosync').then(()=>app.listen(process.env.PORT||4000,()=>console.log(`BioSync backend running on http://localhost:${process.env.PORT||4000}`))).catch(e=>{console.error('MongoDB connection failed:',e.message);process.exit(1)});
