require('dotenv').config();
const express = require('express');
const cors = require('cors');
const { createClient } = require('@supabase/supabase-js');

const app = express();
const port = process.env.PORT || 3000;

// Configure CORS to allow requests from the frontend
app.use(cors());

// Parse JSON request bodies
app.use(express.json());

// Initialize Supabase Client
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseUrl.startsWith('http') || supabaseUrl.includes('your_supabase_url_here')) {
  console.error("❌ LỖI: SUPABASE_URL không hợp lệ. Vui lòng kiểm tra lại file .env (nhớ Ctrl+S để lưu file) và đảm bảo bạn đã nhập đúng URL bắt đầu bằng https://");
  process.exit(1);
}

if (!supabaseKey || supabaseKey.includes('your_supabase_anon_key_here')) {
  console.error("❌ LỖI: SUPABASE_ANON_KEY không hợp lệ. Vui lòng kiểm tra lại file .env (nhớ Ctrl+S để lưu file) và đảm bảo bạn đã nhập đúng Key.");
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

// --- MIDDLEWARES ---

// Middleware: Verify JWT Token
const verifyToken = async (req, res, next) => {
  try {
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ error: 'Không tìm thấy token hoặc sai định dạng' });
    }

    const token = authHeader.split(' ')[1];
    
    // Sử dụng supabase.auth.getUser(token) để xác thực
    const { data, error } = await supabase.auth.getUser(token);

    if (error || !data.user) {
      return res.status(401).json({ error: 'Token không hợp lệ hoặc đã hết hạn' });
    }

    // Gán thông tin user vào req
    req.user = data.user;
    next();
  } catch (err) {
    res.status(500).json({ error: 'Lỗi server khi xác thực token', details: err.message });
  }
};

// Middleware: Require Admin Role
const requireAdmin = async (req, res, next) => {
  try {
    if (!req.user || !req.user.id) {
      return res.status(401).json({ error: 'Người dùng chưa được xác thực' });
    }

    // Truy vấn bảng profiles để kiểm tra role
    const { data: profile, error } = await supabase
      .from('profiles')
      .select('role')
      .eq('id', req.user.id)
      .single();

    if (error || !profile) {
      if (error && error.code === 'PGRST116') {
        return res.status(403).json({ error: 'Người dùng không có profile. Truy cập bị từ chối.' });
      }
      return res.status(500).json({ error: 'Không thể lấy thông tin profile của người dùng', details: error ? error.message : '' });
    }

    if (profile.role !== 'admin') {
      return res.status(403).json({ error: 'Truy cập bị từ chối. Cần quyền admin.' });
    }

    next();
  } catch (err) {
    res.status(500).json({ error: 'Lỗi server khi kiểm tra quyền admin', details: err.message });
  }
};

// Basic test route
app.get('/', (req, res) => {
  res.send('Hello from the Express server!');
});

// Example route using Supabase
app.get('/api/test-db', async (req, res) => {
  try {
    // You can query your tables here, e.g.:
    // const { data, error } = await supabase.from('your_table').select('*');
    res.json({ message: 'Supabase client is initialized successfully.', supabaseUrl: supabaseUrl ? 'Set' : 'Not Set' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Register route
app.post('/api/auth/register', async (req, res) => {
  const { email, password, full_name } = req.body;

  if (!email || !password) {
    return res.status(400).json({ error: 'Email và password là bắt buộc' });
  }

  try {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: full_name || '',
        }
      }
    });

    if (error) {
      // Supabase trả về lỗi nếu user đã tồn tại hoặc mật khẩu yếu, v.v.
      return res.status(400).json({ error: error.message });
    }

    res.status(201).json({
      message: 'Đăng ký thành công',
      user: data.user,
    });
  } catch (err) {
    res.status(500).json({ error: 'Lỗi server nội bộ', details: err.message });
  }
});

// Login route
app.post('/api/auth/login', async (req, res) => {
  const { email, password } = req.body;

  if (!email || !password) {
    return res.status(400).json({ error: 'Email và password là bắt buộc' });
  }

  try {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      // Sai tài khoản, sai mật khẩu, v.v.
      return res.status(401).json({ error: error.message });
    }

    res.status(200).json({
      message: 'Đăng nhập thành công',
      access_token: data.session.access_token,
      user: data.user,
    });
  } catch (err) {
    res.status(500).json({ error: 'Lỗi server nội bộ', details: err.message });
  }
});

// --- USER ROUTES ---

// Lấy thông tin profile của user đang đăng nhập
app.get('/api/users/profile', verifyToken, async (req, res) => {
  try {
    const { data: profile, error } = await supabase
      .from('profiles')
      .select('*')
      .eq('id', req.user.id)
      .single();

    if (error) {
      if (error.code === 'PGRST116') {
        return res.status(404).json({ error: 'Không tìm thấy profile cho người dùng này. Vui lòng đăng ký tài khoản mới để hệ thống tự động tạo profile.' });
      }
      return res.status(500).json({ error: 'Không thể lấy thông tin profile', details: error.message });
    }

    res.status(200).json({ profile });
  } catch (err) {
    res.status(500).json({ error: 'Lỗi server', details: err.message });
  }
});

// Lấy danh sách toàn bộ user (Chỉ dành cho Admin)
app.get('/api/users/all', verifyToken, requireAdmin, async (req, res) => {
  try {
    const { data: profiles, error } = await supabase
      .from('profiles')
      .select('*');

    if (error) {
      return res.status(500).json({ error: 'Không thể lấy danh sách người dùng', details: error.message });
    }

    res.status(200).json({ users: profiles });
  } catch (err) {
    res.status(500).json({ error: 'Lỗi server', details: err.message });
  }
});

app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});
