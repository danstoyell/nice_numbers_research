// Exact bounded search kernel. Compile with clang++ -O3 -std=c++17.
// Deliberately limited to b <= 30 and n < 1e9 to avoid arithmetic overflow.
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <vector>
using u64=std::uint64_t;
using u128=__uint128_t;

bool nice(u64 n,unsigned b) {
    u64 seen=0;
    unsigned count=0;
    u128 square=u128(n)*n;
    u128 powers[2]={square,square*n};
    for (auto value:powers) {
        do {
            unsigned digit=unsigned(value%b);
            value/=b;
            u64 bit=u64(1)<<digit;
            if(seen&bit) return false;
            seen|=bit;
            ++count;
        } while(value);
    }
    return count==b && seen==((u64(1)<<b)-1);
}

int main(int argc,char** argv) {
    if(argc!=4) return 2;
    unsigned b=std::strtoul(argv[1],nullptr,10);
    u64 lo=std::strtoull(argv[2],nullptr,10);
    u64 hi=std::strtoull(argv[3],nullptr,10);
    if(b<2 || b>30 || lo<1 || hi>=1000000000ULL || lo>hi) return 3;
    auto start=std::chrono::steady_clock::now();
    u64 modulus=u64(b)*(b-1), target=u64(b)*(b-1)/2;
    std::vector<u64> residues,solutions;
    for(u64 r=0;r<modulus;++r) {
        if((r*r*(r+1))%(b-1)!=target%(b-1)) continue;
        if((r*r)%b==(r*r*r)%b) continue;
        residues.push_back(r);
    }
    u64 checked=0;
    for(auto r:residues) {
        u64 first=lo+(r+modulus-lo%modulus)%modulus;
        for(u64 n=first;n<=hi;n+=modulus) {
            ++checked;
            if(nice(n,b)) solutions.push_back(n);
        }
    }
    double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
    std::cout<<"{\"base\":"<<b<<",\"lo\":"<<lo<<",\"hi\":"<<hi
             <<",\"interval_count\":"<<(hi-lo+1)<<",\"crt_modulus\":"<<modulus
             <<",\"surviving_residues\":"<<residues.size()
             <<",\"checked\":"<<checked<<",\"seconds\":"<<sec
             <<",\"solutions\":[";
    for(unsigned i=0;i<solutions.size();++i) {
        if(i) std::cout<<",";
        std::cout<<solutions[i];
    }
    std::cout<<"]}\n";
}
