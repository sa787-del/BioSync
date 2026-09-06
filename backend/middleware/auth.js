function requireAuth(req,res,next){if(!req.session.user)return res.status(401).json({message:'Authentication required'});next()}
function requireRole(...roles){return (req,res,next)=>{if(!req.session.user)return res.status(401).json({message:'Authentication required'});if(!roles.includes(req.session.user.role))return res.status(403).json({message:'You do not have access to this area'});next()}}
module.exports={requireAuth,requireRole};
