package com.portfolio.quant.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.provisioning.InMemoryUserDetailsManager;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
public class SecurityConfig {

    @Bean
    SecurityFilterChain securityFilterChain(
            HttpSecurity http,
            @Value("${quant.security.enabled:false}") boolean securityEnabled
    ) throws Exception {
        http.csrf(csrf -> csrf.disable());
        if (securityEnabled) {
            http.authorizeHttpRequests(auth -> auth
                    .requestMatchers("/actuator/health", "/actuator/info").permitAll()
                    .anyRequest().authenticated()
            ).httpBasic(basic -> basic.realmName("quant-platform"));
        } else {
            http.authorizeHttpRequests(auth -> auth.anyRequest().permitAll());
        }
        return http.build();
    }

    @Bean
    UserDetailsService userDetailsService(
            @Value("${quant.security.username}") String username,
            @Value("${quant.security.password}") String password,
            PasswordEncoder passwordEncoder
    ) {
        UserDetails user = User.withUsername(username)
                .password(passwordEncoder.encode(password))
                .roles("RESEARCHER")
                .build();
        return new InMemoryUserDetailsManager(user);
    }

    @Bean
    PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}