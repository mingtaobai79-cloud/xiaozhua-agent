## SPI开发说明
多模块项目，module 会被编译成一个spi 的jar

1、spi_info.json
```
{
  "scopes": ["spi-app-name"]
}
```

scope: spi组件的适配范围，ALL 针对所有应用， ctp-user等具体的应用code

2、spring.factories
~~~
com.seeyon.cip.connector.api.sso.SsoService=\
com.seeyon.extend.spi.sso.TemplateSsoServiceImpl
~~~
格式：
api包里面的接口全路径=手写实现代码的全路径

3、添加三方jar
三方依赖jar 统一放到 /third-jar文件夹下面

依赖引入

scope: system

systemPath: ${project.basedir}/third-jar/XXXX.jar

demo pom引入
~~~
<dependency>
    <groupId>com.aliyun.oss</groupId>
    <artifactId>aliyun-sdk-oss</artifactId>
    <version>3.17.4</version>
    <scope>system</scope>
    <systemPath>${project.basedir}/third-jar/aliyun-sdk-oss-3.18.1.jar</systemPath>
</dependency>
~~~

## 客开SPI限制

### 文件SPI扩展
1、当前客开通路不支持文件SPI扩展

2、文件存储spi扩展通路

2.1 本地构建打包jar

2.2 上传到对应的存储  1、磁盘  2、nexus

2.3 修改对应服务的nacos - 磁盘
```yaml
seeyon:
  spi:
    enable: true
  file:
    storage-type: spi
    spiPlugins: 
    - file: /xxx/xxx/xxx.jar

```
2.4 修改对应服务的nacos - nexus
```yaml
seeyon:
  spi:
    enable: true
  file:
    storage-type: spi
    spiPlugins: 
    - maven:com.seeyon,boot-starter-file-spi,1.0.0
  dynamic:
    loader:
      type: maven
      maven:
        releaseUrl: http://ip:端口/repository/maven-releases/
        snapshotUrl: http://ip:端口/repository/maven-snapshots/
        username: 账号
        password: 密码

```

3、重启对应的服务