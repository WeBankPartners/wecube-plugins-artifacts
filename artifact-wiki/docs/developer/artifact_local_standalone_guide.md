# Artifact 快速本地启动环境配置

## 步骤
1. 安装JDK
	
	需要在开发电脑上先安装JDK，请参考[JDK安装文档](jdk_install_guide.md)

	需要在开发电脑上先安装Maven，请参考[Maven安装文档](maven_install_guide.md)

2. 克隆Artifact代码
	
	```shell script
    git clone git@github.com:WeBankPartners/wecube-plugins-artifacts.git
    ```

3. 运行本地编译
	
    ```shell script
     cd wecube-plugins-artifacts
     mvn clean package -Dmaven.test.skip=true
    ```

4. 启动本地快速体验包
    ```shell script
    java -jar -Dspring.profiles.active=ch-local artifacts-core/target/artifacts-core-*.jar
    ```

5. 打开浏览器，输入下面的URL,即可体验Artifacts功能  
  
   [http://localhost:9080/Artifacts/](http://localhost:9080/Artifacts/)
    
