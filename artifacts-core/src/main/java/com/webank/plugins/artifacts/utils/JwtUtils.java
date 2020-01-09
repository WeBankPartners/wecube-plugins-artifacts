package com.webank.plugins.artifacts.utils;

import org.apache.commons.lang3.StringUtils;

import com.webank.plugins.artifacts.constant.ArtifactsConstants;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.Jws;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;

public class JwtUtils {
    
    public static String getAuthUserName(String sAccessTokenHeader) {
        String sAccessToken = sAccessTokenHeader.substring(ArtifactsConstants.PREFIX_BEARER_TOKEN.length()).trim();

        if (StringUtils.isBlank(sAccessToken)) {
            throw new JwtException("Access token is blank.");
        }
        Jws<Claims> jwt = null;
        try {
            jwt = Jwts.parser().setSigningKey(StringUtilsEx.decodeBase64(ArtifactsConstants.SIGNING_KEY)).parseClaimsJws(sAccessToken);
        } catch (ExpiredJwtException e) {
            throw new JwtException("Access token has expired.");
        }

        Claims claims = jwt.getBody();

        String username = claims.getSubject();
        return username;
    }
}
