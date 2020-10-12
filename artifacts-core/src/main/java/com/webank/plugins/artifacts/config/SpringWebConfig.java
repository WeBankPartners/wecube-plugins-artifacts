package com.webank.plugins.artifacts.config;

import javax.servlet.Filter;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import com.webank.plugins.artifacts.auth.filter.Http401AuthenticationEntryPoint;
import com.webank.plugins.artifacts.auth.filter.JwtClientConfig;
import com.webank.plugins.artifacts.auth.filter.JwtSsoBasedAuthenticationFilter;
import com.webank.plugins.artifacts.commons.ApplicationProperties;
import com.webank.plugins.artifacts.interceptor.ApiAccessInterceptor;

@Configuration
@EnableWebMvc
@EnableWebSecurity
@EnableGlobalMethodSecurity(jsr250Enabled = true, prePostEnabled = true, securedEnabled = true)
@ComponentScan({ "com.webank.plugins.artifacts.controller" })
public class SpringWebConfig extends WebSecurityConfigurerAdapter implements WebMvcConfigurer {

    @Autowired
    private ApiAccessInterceptor apiAccessInterceptor;
    
    @Autowired
    private ApplicationProperties applicationProperties;

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(apiAccessInterceptor).addPathPatterns("/**");
        WebMvcConfigurer.super.addInterceptors(registry);
    }

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        registry.addResourceHandler("/swagger-ui.html").addResourceLocations("classpath:/META-INF/resources/");
        registry.addResourceHandler("/webjars/**").addResourceLocations("classpath:/META-INF/resources/webjars/");
    }
    
    @Override
    protected void configure(HttpSecurity http) throws Exception {
        configureLocalAuthentication(http);

    }
    
    protected void configureLocalAuthentication(HttpSecurity http) throws Exception {
        http.authorizeRequests() //
                .antMatchers("/swagger-ui.html/**", "/swagger-resources/**").permitAll()//
                .antMatchers("/webjars/**").permitAll() //
                .antMatchers("/v2/api-docs").permitAll() //
                .antMatchers("/csrf").permitAll() //
                .anyRequest().authenticated() //
                .and()//
                .addFilter(jwtSsoBasedAuthenticationFilter())//
                .csrf()//
                .disable() //
                .exceptionHandling() //
                .authenticationEntryPoint(new Http401AuthenticationEntryPoint()); //
    }

    protected Filter jwtSsoBasedAuthenticationFilter() throws Exception {
        JwtClientConfig jwtClientConfig = new JwtClientConfig();
        jwtClientConfig.setSigningKey(applicationProperties.getJwtSigningKey());
        JwtSsoBasedAuthenticationFilter f = new JwtSsoBasedAuthenticationFilter(authenticationManager(),
                jwtClientConfig);
        return (Filter) f;
    }

}
