package com.api.utils;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;

import java.util.HashMap;
import java.util.Map;

public class HttpTest {
    public static String search(String query,String address,String room_num,String size){
        Map<String,String> params = new HashMap<>();
        // Request parameters
        String user_id = "";
        String token = "";

        params.put("user_id",user_id);
        params.put("query",query);
        params.put("address",address);
        params.put("room_num",room_num);
        params.put("size",size);
        params.put("token",token);

        // Send the search user request,
        // assuming that the returned string result is the above JSON string
        String result = HttpClientUtil.doPost("http://39.102.48.55:3389/price_p",params);
        return result;
    }

    public static void main(String[] args) {
        house_type = ""
        house_place = ""
        house_size = ""
        house_number = ""
        String result = HttpTest.search(house_type, house_place, house_size, house_number);
        System.out.println(result);
    }
}
