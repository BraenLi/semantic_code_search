/* C API handler for HTTP requests */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    char* method;
    char* path;
    char* body;
} Request;

typedef struct {
    int status_code;
    char* content_type;
    char* body;
} Response;

Response* create_response(int status, const char* body) {
    Response* resp = malloc(sizeof(Response));
    resp->status_code = status;
    resp->body = strdup(body);
    resp->content_type = "application/json";
    return resp;
}

Response* handle_login_request(Request* req) {
    /* Parse login credentials and authenticate */
    if (strcmp(req->method, "POST") != 0) {
        return create_response(405, "{\"error\": \"Method not allowed\"}");
    }
    /* Process login logic here */
    return create_response(200, "{\"status\": \"logged in\"}");
}

Response* handle_user_registration(Request* req) {
    /* Handle new user registration */
    if (strcmp(req->method, "POST") != 0) {
        return create_response(405, "{\"error\": \"Method not allowed\"}");
    }
    /* Process registration logic here */
    return create_response(201, "{\"status\": \"user created\"}");
}

void free_response(Response* resp) {
    if (resp) {
        free(resp->body);
        free(resp);
    }
}
