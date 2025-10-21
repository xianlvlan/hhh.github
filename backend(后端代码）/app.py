# 导入依赖
from flask import Flask, request, jsonify
from flask_cors import CORS  # 跨域处理
import pymysql  # 连接MySQL
import bcrypt  # 密码加密
from datetime import datetime  # 处理时间

# 初始化Flask应用
app = Flask(__name__)

# 配置跨域：允许前端GitHub Pages地址访问（替换为你的前端URL，如 "https://xxx.github.io"）
# 本地测试时可先用 "*" 允许所有域名（生产环境必须指定具体域名）
CORS(app, origins="*")

# --------------------------
# 数据库连接函数（复用连接）
# --------------------------
def get_db_connection():
    # 连接本地MySQL（部署到服务器时需改host为服务器地址）
    conn = pymysql.connect(
        host='localhost',    # 数据库地址（本地是localhost）
        user='root',         # 用户名（默认root）
        password='971264751Ztt@',   # 你的MySQL密码（改成自己的！）
        database='myproject',# 数据库名（和前面创建的一致）
        charset='utf8mb4',   # 字符集
        cursorclass=pymysql.cursors.DictCursor  # 让查询结果返回字典格式
    )
    return conn

# --------------------------
# 测试接口（验证后端是否运行）
# --------------------------
@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({
        'code': 200,
        'message': '后端接口正常工作！'
    })

# --------------------------
# 用户注册接口（前端调用这个接口提交注册信息）
# --------------------------
@app.route('/api/register', methods=['POST'])
def register():
    # 1. 获取前端提交的JSON数据（username, password, email）
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    # 2. 简单验证：检查必填字段是否为空
    if not all([username, password, email]):
        return jsonify({
            'code': 400,
            'message': '用户名、密码、邮箱不能为空！'
        })

    # 3. 连接数据库，检查用户名/邮箱是否已存在
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 查用户名是否存在
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            if cursor.fetchone():  # 如果查到数据，说明用户名已存在
                return jsonify({
                    'code': 400,
                    'message': '用户名已被注册！'
                })
            
            # 查邮箱是否存在
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            if cursor.fetchone():
                return jsonify({
                    'code': 400,
                    'message': '邮箱已被注册！'
                })

            # 4. 密码加密（用bcrypt，比md5安全，自动加盐）
            # 注意：password需要转成bytes类型
            password_bytes = password.encode('utf-8')
            # 生成加密后的密码（哈希值）
            hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
            # 转成字符串存储（数据库存字符串）
            hashed_password_str = hashed_password.decode('utf-8')

            # 5. 插入数据到users表
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 当前时间
            cursor.execute(
                '''
                INSERT INTO users (username, password, email, create_time)
                VALUES (%s, %s, %s, %s)
                ''',
                (username, hashed_password_str, email, current_time)
            )
            conn.commit()  # 提交事务

        # 6. 注册成功，返回结果
        return jsonify({
            'code': 200,
            'message': '注册成功！'
        })

    except Exception as e:
        # 出错时回滚事务
        conn.rollback()
        return jsonify({
            'code': 500,
            'message': f'服务器错误：{str(e)}'
        })
    finally:
        # 关闭数据库连接
        conn.close()

# --------------------------
# 启动后端服务器
# --------------------------
if __name__ == '__main__':
    # 本地开发时用debug=True（自动重启），host='0.0.0.0'允许同一局域网访问
    app.run(host='0.0.0.0', port=5000, debug=True)