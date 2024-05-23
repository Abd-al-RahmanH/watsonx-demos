class SampleJava{
    void sayHello(){
        System.out.println("hello world")
    }

    void sayHelloworld(){
        System.out.println("hello world")
    }

    void calc(){
        int i = 1;
        int answer = 1;
        for(i=1;i<1000000;i++)
            answer = answer * i;
        sayHello();
    }
}