# SPI动态注册组件
## 1. 组件介绍

   spi组件提供了基于SpringBoot SPI机制进行客开扩展的能力
   
## 2. 配置说明
application.yaml
```yaml
seeyon:
  spi:
    enable: true # 是否启用
    spi-plugins:
      - maven:com.seeyon,xxx-spi-providers,1.0.0 # 定义SPI接口实现的jar包maven GAV坐标，格式：maven:group,artifactId,version
      - file:/var/spi/demo-order/xxx.jar # 定义SPI接口实现的jar包的存放路径，格式：file:jar包的文件路径（window路径目录之间也是用/连接）
      - oss:com.seeyon,xxx-spi-providers,1.0.0 # 定义SPI接口实现的jar包 格式：oss:group,artifactId,version  oss存放位置：摆渡桶：spi/com/seeyon/xxx-spi-providers/1.0.0/xxx-spi-providers-1.0.0.jar
```
   
## 3. 组件使用

### 3.1 maven坐标
```
<dependency>
    <groupId>com.seeyon</groupId>
    <artifactId>boot-starter-spi</artifactId>
</dependency>
```
### 3.2 组件使用
1. 主应用通过maven坐标引入spi组件
2. 建立spi的maven工程并实现对应spi接口
3. 在spi工程的resources/META-INF下创建spring.factories文件，并定义实现的接口以及实现类
4. 通过Nacos配置（支持动态更新加载）或本地application yaml配置对应的spi-plugins配置
5. 监听spi实现类动态加载的Event，刷新本地cache或标记（事件中的spi实现类对象已经注入到Spring ApplicationContext中）

spring.factories样例如下：
```
com.seeyon.demo.Demo=\
com.seeyon.kekai.DemoImpl
com.seeyon.demo.Demo1=\
com.seeyon.kekai.Demo1Impl
```

SPIProviderRegistEvent事件定义如下：
```java
public class SPIProviderRegisterEvent implements Serializable {
    /**
     * SPI接口类名称 fullName
     */
    private String interfaceName;
    /**
     * SPI接口实现类对象列表（客开增加的实现类对象）
     */
    private List spiProviders;
}
```
