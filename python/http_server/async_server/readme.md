模仿asyncio实现的一个简单的协程机制  
~~todo：允许多个协程对同一个fd注册~~  
v2版重构了服务器，新创建TASK来处理socket