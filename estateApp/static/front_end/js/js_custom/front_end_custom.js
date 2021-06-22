function queryHouse(q) {
    var x = String(q.name);
    var data= {
        data: JSON.stringify({
            'x': x
        }),
    };
    $.ajax({
        url:"{{ url_for('search_result', query='1') }}",
        type:"post",
        data:data,
        dataType: 'json',
        success:function(data){
             //成功后的一些操作
            {{ print('aaa')}}

        },
        // error:function(e){
        //      alert("error");
        // }
    })
}