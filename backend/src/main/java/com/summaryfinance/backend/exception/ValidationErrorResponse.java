package com.summaryfinance.backend.exception;

import lombok.Data;
import lombok.EqualsAndHashCode;
import java.util.Map;

@Data
@EqualsAndHashCode(callSuper = true)
public class ValidationErrorResponse extends ErrorResponse {
    private final Map<String, String> errors;
    
    public ValidationErrorResponse(String message, Map<String, String> errors) {
        super(message);
        this.errors = errors;
    }
} 